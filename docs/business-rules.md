# Regras de Negocio MindEdu

## Escopo pedagogico

- Produto educativo de habilidades socioemocionais para crianças de até 12 anos.
- As atividades devem ser mediadas por um educador ou adulto de confiança.
- Não é terapia, não faz diagnóstico e não fornece aconselhamento clínico.

## Autenticacao

- Cadastro exige: email, username, senha >= 8.
- Login aceita apenas: `user_id + senha`.
- `user_id` e gerado automaticamente no formato `MDU-XXXX-XXXX`.
- Recuperacao com token/codigo e resposta anti-enumeracao.

## Privacidade e seguranca

- Dados minimos LGPD: email, username, user_id, hash de senha.
- Hash de senha: argon2id.
- JWT access/refresh com rotacao de refresh.
- Sem texto livre em missao/resposta no MVP.
- Filtro de dados pessoais pronto para v1 (`pii_filters.py`).
- O resumo educativo individual não mostra o conteúdo dos check-ins; cada visualização administrativa fica registrada na auditoria.

## UxU (nucleo)

- Missao: categoria, intensidade, tags, want_now.
- Resposta: carta aprovada + acoes guiadas.
- Feedback: util / nao ajudou + melhor resposta.
- Auto-resposta na propria missao e bloqueada.
- Missao expira por padrao em 48h.
- Sem DM e sem chat aberto no MVP.

## Gamificacao

- XP prioriza cooperacao util.
- Ranking interno por faixa (sem leaderboard publico nominal).
- Mascote evolutivo com inventario cosmetico.

## Moderacao

- Denuncia por alvo e motivo.
- Pipeline padrao: aviso -> mute -> ban.
- Bloqueio entre usuarios.
- Toda acao administrativa gera auditoria.

## Rate limits MVP

- register: 5/h por IP.
- login: 10/15min por IP.
- checkins:create: 12/dia por usuario.
- missions:create: 5/dia por usuario.
- missions:respond: 30/dia por usuario.
- reports:create: 20/dia por usuario.

## Relatorio PDF

- Exporta progresso educacional agregado por periodo.
- Inclui trilhas/licoes, habito de check-in e cooperacao agregada.
- Sem diagnostico e sem detalhes sensiveis.
