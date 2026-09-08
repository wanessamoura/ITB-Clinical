# ITB Clinical — Versão 1.0

Aplicativo de apoio à triagem clínica e à mensuração do Índice Tornozelo-Braquial (ITB).

## Principais recursos da versão 1.0
- Cabeçalho institucional do Centro de Pesquisa Clínica.
- Identificação por protocolo/estudo, sujeito e avaliador.
- Data e horário registrados automaticamente no momento do salvamento, sem edição manual.
- Avaliação de sintomas, achados de pele, pulsos periféricos e pressões sistólicas.
- Cálculo automático do ITB direito e esquerdo.
- Classificação visual: anormal em vermelho, limítrofe em laranja, normal em verde e demais estados sinalizados separadamente.
- Elegibilidade com sintomas de claudicação nos últimos 12 meses e critério automático `ITB < 0,90`.
- Validação dos campos obrigatórios antes do salvamento.
- Relatório PDF com cabeçalho institucional, assinatura do avaliador, referência da diretriz, observação sobre protocolos específicos e rodapé de versão/rastreabilidade.
- Segunda via do PDF pela área administrativa.
- Banco de dados protegido por senha para visualização e exportação.
- Exportação CSV e Excel organizada.

## Senha administrativa
No Streamlit Community Cloud, configure em **Settings > Secrets**:

```toml
ADMIN_PASSWORD = "sua-senha-forte"
```

Não coloque a senha diretamente no `app.py` nem a envie ao GitHub.

## Observação sobre armazenamento
O SQLite local é adequado para prototipagem/testes. Para uso real com dados identificáveis de participantes, o armazenamento deve ser avaliado conforme requisitos institucionais, éticos, de segurança e LGPD.
