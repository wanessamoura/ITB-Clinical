# ITB-Enf v2

Protótipo acadêmico de sistema web para mensuração, cálculo, registro e relatório do Índice Tornozelo-Braquial.

## Recursos
- Interface web responsiva para uso em celular.
- Cadastro do equipamento utilizado, modelo, patrimônio/ID e manguito.
- Cálculo automático do ITB direito e esquerdo.
- Classificação automática.
- Banco de dados local SQLite.
- Visualização das avaliações.
- Exportação do banco em CSV.
- Geração de relatório individual em PDF.

## Instalação
Python 3.10+ recomendado.

```bash
pip install -r requirements.txt
streamlit run app.py
```

O sistema abre no navegador.

## Observação sobre dados
Este protótipo usa SQLite local. Para pesquisa clínica real, o banco deverá ser hospedado em ambiente institucional seguro, com controle de acesso, minimização de dados identificáveis, política de retenção e avaliação de conformidade ética/LGPD.

## PDF
A geração do PDF utiliza o ReportLab, biblioteca open source para criação de documentos PDF em Python.
