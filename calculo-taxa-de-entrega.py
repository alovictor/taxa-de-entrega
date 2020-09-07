import requests
import pandas as pd
from bs4 import BeautifulSoup

def pedir_endereços():

    enderecos = {'origens' : [],
                 'destinos' : []}
    
    while True:
        origem = input('Qual é o endereço inicial?\n')
        if origem == '':
            continue
        else:
            enderecos['origens'].append(origem)
            break

    while True:
        resposta = input('\nGostaria de adicionar uma parada? S -> SIM | N -> NÃo\n').lower()
        if resposta == 's':
            while True:
                parada = input('Qual é o endereço do ponto de parada?\n')
                if parada == '':
                    continue
                else:
                    enderecos['destinos'].append(parada)
                    enderecos['origens'].append(parada)
                    break        
        elif resposta == 'n':
            break
        else:
            print('Tente novamente\n')
            continue
    
    while True:
        destino = input('\nQual é o endereço final?\n')
        if destino == '':
            continue
        else:
            enderecos['destinos'].append(destino)
            break

    return enderecos

def obter_precos_combustiveis():
        
    dados = {'Tipo' : [], 'Valor' : []}

    page = requests.get("https://precodoscombustiveis.com.br/pt-br/city/brasil/amazonas/manaus/112?page=1")
    soup = BeautifulSoup(page.content, "html.parser")

    results = soup.find('div', class_= 'pr-md-5').find_all('div', class_= 'card')

    for result in results:
        combustivel = result.div.span.text
        preco = result.div.contents[7].text

        dados['Tipo'].append(combustivel)
        dados['Valor'].append(preco)

    tabela_combustiveis = pd.DataFrame(dados)
    gasolina =  tabela_combustiveis.at[0, 'Valor']
    preco = float(gasolina[3:])
    return preco

def obter_distancia_maps_api():

    def formatador(lista):
        final = ''
        j = len(lista)
        for endereco in lista:
            final += endereco
            if j >= 2:
                final += '|'
            j -= 1
        final = final.replace(' ', '+')
        return final

    enderecos = pedir_endereços()

    origens = enderecos['origens']
    destinos = enderecos['destinos']

    api_key = "[YOUR API KEY]"
    origem = formatador(origens)
    destino = formatador(destinos)

    result = requests.get(f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={api_key}").json()

    trajetos = pd.DataFrame({'distancias' : [], 'tempos' : []})
    distancia = [] # KM
    tempo = []     # MIN

    for item in result.items():
            if item[0] == 'rows':
                rows = item[1]
                for item in rows:
                    elements = list(item.values())
                    for item in elements:
                        for dicionario in item:
                            for item in dicionario.items():
                                if item[0] == 'distance':
                                    distancia.append(item[1]['text'])
                                if item[0] == 'duration':
                                    tempo.append(item[1]['text'])

    final = pd.DataFrame({'distancias': distancia, 'tempos' : tempo})
    final.index = range(1,(pow(len(origens), 2) + 1))

    for index in range(1, len(origens) + 1):
        if index == 1:
            trajetos = trajetos.append(final.loc[[index]], ignore_index = True)
        elif index == len(origens):
            index = pow(index, 2)
            trajetos = trajetos.append(final.loc[[index]], ignore_index = True)
        else:
            index = pow(index, 2) + 2
            trajetos = trajetos.append(final.loc[[index]], ignore_index = True)

    calculos = trajetos.copy()
    calculos = calculos.applymap(lambda x: float(x.strip(' kmins')))

    distancia_total = round(calculos.sum()[0], 2)
    tempo_total = round(calculos.sum()[1], 2)

    return trajetos, distancia_total, tempo_total

def main():
    tabela_trajetos, distancia, tempo = obter_distancia_maps_api()

    rendimento_veiculo = [km/l]
    preco_gasolina = obter_precos_combustiveis()

    taxa_entrega = ((distancia/rendimento_carro) * preco_gasolina)

    valor_taxa = round(taxa_entrega, 2)

    print('\n\n')
    print('****************************************************************')
    print(f'Você vai percorrer {distancia} km')
    print(f'O tempo médio de duração do trajeto é de {tempo} minutos')
    print(f'\nTaxa de entrega: R${taxa_entrega}')
    print('****************************************************************')

if __name__ == '__main__':
    main()