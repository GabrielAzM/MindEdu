# Deploy do MindEdu no Render

Este repositório inclui um Blueprint em `render.yaml` que cria a API FastAPI e o frontend Vite como serviços separados. A API usa SQLite; o Blueprint monta um disco persistente em `/var/data` para manter o banco, os PDFs exportados e a fila local de recuperação entre deploys.

## Requisitos

- Repositório enviado para GitHub, GitLab ou outro provedor conectado ao Render.
- Conta/workspace Render com plano pago para a API, porque o Render exige um serviço pago para anexar disco persistente. O site estático pode usar o plano gratuito.
- Acesso aos segredos de ambiente do serviço da API após o primeiro deploy.

O banco SQLite é configurado para uma única instância da API. Não aumente o número de instâncias enquanto o projeto usar esse banco.

## Criar os serviços

1. Envie as alterações para um branch do repositório remoto.
2. No Render, escolha **New → Blueprint** e conecte o repositório e o branch.
3. O Render localizará `render.yaml`. Revise os serviços `mindedu-api` e `mindedu-web` e confirme a criação.
4. Aguarde os dois deploys. O health check da API é `https://mindedu-api.onrender.com/health`; a página da API também oferece `/docs`.
5. Abra a URL pública de `mindedu-web` e confira a aplicação.

O serviço Python está fixado em Python 3.12.11. O site instala dependências com `npm ci` a partir do lockfile e publica `frontend/dist`.

## Conferir os endereços

O Blueprint usa `https://mindedu-api.onrender.com` para o frontend e `https://mindedu-web.onrender.com` para o CORS da API. Depois de criar os serviços, confira as URLs atribuídas pelo Render. Se alguma URL for diferente:

1. No serviço `mindedu-web`, ajuste `VITE_API_URL` para a URL pública real da API.
2. No serviço `mindedu-api`, ajuste `MINDEDU_CORS_ORIGINS` para a origem pública real do frontend, sem barra no final.
3. Faça um deploy dos dois serviços para aplicar as alterações. `VITE_API_URL` é incorporada durante o build do frontend.

## Primeiro acesso administrativo

- ID de acesso inicial: `MDU-ADMIN-0001`.
- A senha inicial é gerada pelo Render na variável `MINDEDU_ADMIN_PASSWORD` do serviço `mindedu-api`. Consulte e guarde esse valor antes de compartilhar o endereço do sistema.
- O administrador inicial só é criado quando o banco ainda não possui uma conta administrativa. Alterar a variável depois disso não troca a senha gravada no banco.
- Mantenha `MINDEDU_JWT_SECRET` e `MINDEDU_ADMIN_PASSWORD` fora do repositório. O serviço interrompe a inicialização em produção se detectar os segredos padrão, curtos ou uma origem CORS local.

Novos cadastros ficam pendentes até aprovação administrativa, conforme o fluxo atual do sistema.

## Dados persistentes

O disco de 1 GB é montado em `/var/data` e é usado por:

- `MINDEDU_DB_FILE=/var/data/mindedu.db` — banco SQLite.
- `MINDEDU_EXPORT_DIR=/var/data/exports` — PDFs de relatórios.
- `MINDEDU_RECOVERY_OUTBOX_PATH=/var/data/recovery_outbox.log` — códigos gerados pelo fluxo de recuperação.

O sistema ainda não envia mensagens por e-mail. Os pedidos de recuperação gravam os códigos na outbox local em texto; portanto, configure um provedor de e-mail e substitua esse mecanismo antes de depender de recuperação automática de contas em produção. Restrinja o acesso ao disco e nunca compartilhe o conteúdo da outbox.

## Atualizações e verificação

Com deploy automático habilitado, novos commits no branch conectado iniciam novos deploys. Após cada deploy:

1. Confirme que `https://mindedu-api.onrender.com/health` retorna `{"status":"ok"}`.
2. Abra o frontend e confira login, trilhas, mascote e carregamento dos dados da API.
3. Entre como administrador e aprove um cadastro de teste.
4. Gere e baixe um relatório para confirmar a escrita e leitura do PDF no disco persistente.
5. Verifique os logs do serviço da API se o health check falhar.

## Alterações no Blueprint

Se renomear os serviços ou usar domínios próprios, atualize também `VITE_API_URL` e `MINDEDU_CORS_ORIGINS`. Não altere o caminho do disco sem apontar as três variáveis de armazenamento para o novo mount path.

Referências oficiais: [Blueprints](https://render.com/docs/blueprint-spec), [discos persistentes](https://render.com/docs/disks), [versões Python](https://render.com/docs/python-version) e [sites estáticos](https://render.com/docs/static-sites).
