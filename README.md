# MindEdu

MindEdu e uma plataforma educativa com foco em cooperacao segura usuario-usuario (UxU) para criancas e adolescentes.

## Stack

- Frontend: React + TypeScript + Vite + React Router + TanStack Query + Zustand + Tailwind + shadcn/ui + Radix + RHF + Zod + Recharts + Framer Motion + PixiJS + Howler (opcional)
- Backend: FastAPI + SQLite + SQLAlchemy + JWT access/refresh
- Contratos: Zod em `shared/schemas` e JSON Schema em `shared/generated`

## Estrutura

- `frontend/`: app React
- `backend/`: API FastAPI e banco local SQLite
- `shared/`: contratos compartilhados
- `docs/`: blueprint e regras

## Executar backend

```bash
cd backend
python -m venv .venv
call .venv\\Scripts\\activate.bat
python -m pip install -e .
uvicorn app.main:app --reload --port 8000
```

Se estiver usando PowerShell:

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -e .
uvicorn app.main:app --reload --port 8000
```

Admin local default (criado no startup se nao existir):

- `user_id`: `MDU-ADMIN-0001`
- `senha`: `Admin12345`

Fluxo de cadastro com aprovacao:

- Novos usuarios entram como `pending` e nao conseguem login ate aprovacao.
- Aprovacao/rejeicao e feita no painel admin (`/admin/moderation`) e registrada em auditoria.
- Dashboard admin principal: `/admin` (atalhos para aprovacao, moderacao e metricas).

Fluxo de missao coop por ID:

- Primeiro envie convite em `Coop` usando `user_id` do parceiro.
- Depois que a amizade ficar `active`, crie missao informando o `user_id` do parceiro (sem feed aberto).
- A pessoa convidada recebe a missao em `Trilhas` com aviso de cooperacao.

Trilhas geradas por XP:

- Agora exibem botao de acesso para iniciar pela primeira licao da trilha gerada.

Controle de XP no quiz:

- Cada envio registra tentativa, mas o XP nao e infinito.
- A primeira tentativa gera XP por desempenho.
- Tentativas seguintes so geram XP ao melhorar a melhor nota anterior.
- Reenvio com mesma nota nao gera XP.

## Executar frontend

```bash
cd frontend
npm install
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

Favicon:

- Coloque a imagem em `frontend/public/faviconmindedu.jpg`.
- O caminho ja esta configurado em `frontend/index.html` e sera carregado automaticamente.

## Banco e seeds

- Schema: `backend/sql/schema.sql`
- Seeds SQL: `backend/sql/seed.sql`
- Seeds JSON: `backend/seeds/*.json`

## Mascotes: onde trocar imagens

Arquivos para sprites animados (PixiJS):

- `frontend/src/assets/mascots/fox/base.webp`, `accessory.webp`, `effect.webp` (+ JSONs correspondentes)
- `frontend/src/assets/mascots/owl/base.webp`, `accessory.webp`, `effect.webp` (+ JSONs correspondentes)

Arquivos para evolucao (4 estagios por mascote):

- `frontend/src/assets/mascots/fox/evolutions/evo1.webp` ate `evo4.webp`
- `frontend/src/assets/mascots/owl/evolutions/evo1.webp` ate `evo4.webp`

Observacao: a referencia desses arquivos fica em `frontend/src/components/pixi/useMascotAssets.ts`.

## Testes

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Troubleshooting Windows (Device Guard)

Se aparecer erro como:

`...\\.venv\\Scripts\\pip.exe foi bloqueado pela politica do Device Guard...`

use sempre:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Importante:

- Nao digite `(.venv)` no inicio do comando. Isso e apenas o prompt do terminal.
- Se ainda bloquear mesmo com `python -m pip`, mova o projeto para uma pasta permitida (ex.: `C:\\dev\\mindedualpha`) e recrie a venv.

## Troubleshooting API (falha ao carregar conteudo)

Se `Home`, `Trilhas`, `Perfil` ou `Admin` exibirem erro de carregamento:

1. Confirme backend ativo em `http://localhost:8000/health`.
2. Confirme `frontend/.env` com `VITE_API_URL=http://localhost:8000`.
3. Faca logout e login novamente (sessao antiga pode expirar).
4. Se persistir, limpe o storage local da chave `mindedu-auth` e entre novamente.

## Aviso de seguranca

MindEdu e educativo. Nao oferece terapia, diagnostico ou aconselhamento clinico.
