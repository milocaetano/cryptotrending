import pandas as pd

data = {
    'Nome': [12, 14, 14],
    'Idade': [25, 30, 40],
    'Cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],    
    'Objeto': { 'Teste': ['123', 'adsf', 'adf'] }
}

df = pd.DataFrame(data)

print( data['Nome'] )

print( data['Nome'][0])
print( data['Objeto'] )
df.head()