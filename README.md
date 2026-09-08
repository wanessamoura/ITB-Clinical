# ITB Clinical

Triagem clínica considerando sintomas de claudicação e medida do Índice Tornozelo-Braquial (ITB).

## Recursos
- Avaliação de sintomas, achados de pele e pulsos periféricos.
- Mensuração e cálculo automático do ITB.
- Medidas podem permanecer em branco ou ser marcadas como “Não avaliado”.
- Banco SQLite, exportação CSV e relatório PDF.
- Interface responsiva para celular.

## Execução
```bash
pip install -r requirements.txt
streamlit run app.py
```

Protótipo destinado ao uso exclusivo por equipe qualificada de pesquisa clínica, como ferramenta de apoio à triagem clínica e à mensuração do ITB.


## Identidade visual
O arquivo `itb_clinical_header.png` é utilizado no cabeçalho do aplicativo e no relatório PDF.


## Atualizações desta versão
- Campo **Protocolo / estudo** no início da identificação, salvo no banco e exibido no relatório PDF.
- Campo de **assinatura do avaliador** no final do PDF, com linha para assinatura, nome e data.
- Migração automática do banco SQLite para acrescentar novos campos sem perder registros anteriores.

- Campo **Instituição / hospital** acima de Protocolo / estudo, incluído no banco e no relatório PDF.


## Área administrativa e exportação CSV

A aba **Banco de dados** é protegida por senha. Usuários sem a senha podem preencher e salvar avaliações, mas não conseguem visualizar nem exportar o banco.

### Uso local
1. Dentro da pasta do projeto, crie a pasta `.streamlit` caso ela não exista.
2. Copie `secrets.example.toml` para `.streamlit/secrets.toml`.
3. Abra `.streamlit/secrets.toml` e substitua o valor de `ADMIN_PASSWORD` por uma senha forte.
4. Não compartilhe esse arquivo e não o envie ao GitHub.

Exemplo:

```toml
ADMIN_PASSWORD = "uma-senha-forte-e-exclusiva"
```

### Streamlit Community Cloud
No painel do aplicativo, abra **App settings / Settings > Secrets** e adicione:

```toml
ADMIN_PASSWORD = "uma-senha-forte-e-exclusiva"
```

A senha não deve ser escrita diretamente no `app.py`.

> Observação: esta proteção restringe a visualização e a exportação pela interface. Para uso real com dados de pesquisa clínica, o armazenamento e o controle de acesso precisam seguir as políticas institucionais, éticas e de LGPD.


## Segunda via do relatório PDF
Na área administrativa, o sistema permite selecionar uma avaliação já salva no banco e gerar novamente o relatório em PDF. Esse recurso é protegido pela mesma senha administrativa usada para visualizar e exportar o banco.


## Referência clínica
A página e o relatório PDF exibem a seguinte nota de fundamentação:

> Cálculo e classificação do Índice Tornozelo-Braquial (ITB) realizados conforme os critérios da 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline for the Management of Lower Extremity Peripheral Artery Disease. Interpretação do ITB de repouso: ≤0,90 anormal; 0,91–0,99 limítrofe; 1,00–1,40 normal; >1,40 não compressível.

Referência principal: Gornik HL et al. 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline for the Management of Lower Extremity Peripheral Artery Disease. Circulation. 2024.


## Correção do acesso administrativo local
Quando não houver `ADMIN_PASSWORD` configurada nos Secrets, é possível criar uma senha
temporária diretamente na aba administrativa. Após a criação, a sessão é autenticada
imediatamente e libera banco de dados, CSV e segunda via em PDF.


## Exportação organizada
A área administrativa agora oferece:
- **CSV organizado**, com nomes de colunas clínicos e ordem lógica.
- **Excel (.xlsx) organizado**, com grupos de colunas, filtros, cabeçalho fixo, larguras ajustadas e formatação para leitura.
