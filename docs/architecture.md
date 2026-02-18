# Arquitetura MindEdu

## Visao geral

- Monorepo com frontend, backend e contratos compartilhados.
- Banco local SQLite com schema orientado a seguranca, moderacao e rastreabilidade.
- API REST com JWT access/refresh e auditoria.
- MVP sem chat livre; UxU estruturado por missoes e cartas.

## Fluxos principais

1. Cadastro -> gera `user_id` -> login com `user_id + senha`.
2. Check-in emocional -> insights + sugestoes.
3. Missao de apoio estruturada -> respostas por carta -> feedback util.
4. Denuncia/bloqueio -> fila de moderacao -> acao admin auditada.
5. Exportacao de relatorio educativo em PDF por periodo.

## Camadas backend

- `api/`: roteadores e contratos HTTP
- `services/`: regras de negocio
- `db/`: conexao e init do banco
- `core/`: seguranca, JWT, rate limit, auditoria
- `utils/`: filtros PII e geracao PDF

## Camadas frontend

- `pages/`: telas
- `services/`: chamadas REST
- `store/`: estado global (auth/mascote/UI)
- `components/`: layout, charts, pixi

## Seguranca

- Senha com argon2id.
- Tokens JWT de curta duracao.
- Recovery anti-enumeracao.
- Rate limit por acao e usuario/IP.
- Logs em `audit_log` para decisoes de moderacao.
