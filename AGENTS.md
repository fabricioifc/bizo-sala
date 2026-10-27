# AGENTS.md — Gestor de Aulas (IFC Videira)

## Contexto
Aplicação web pessoal (usuário único: o professor) para gerenciar turmas, chamadas,
registro de conteúdo, carga horária, notas, recuperação paralela e comunicação por e-mail.

Cursos atendidos:
- **EMI**: Técnico em Informática Integrado ao Ensino Médio (regime anual, 3 trimestres).
- **Graduação**: Bacharelado em Ciência da Computação (regime semestral, 1 ciclo avaliativo).

Referência normativa: *Organização Didática dos Cursos do IFC* (OD). Quando uma regra
abaixo citar um artigo, ele é a fonte; parâmetros que dependem do PPC são configuráveis.

Idioma da interface, do código de domínio e da documentação: português (BR).

## Restrições
- **Custo zero**: nenhum serviço pago. Roda no VPS do professor com Docker.
- **LGPD**: dados de estudantes (inclusive menores) ficam apenas neste sistema.
  Nada de rastreadores/analytics de terceiros. Login obrigatório; HTTPS em produção.
- Usuário único, sem multi-tenant. Simplicidade acima de generalidade.

## Estrutura do repositório
```
backend/    API FastAPI (Python)
frontend/   SPA Vue 3 + PWA (TypeScript)
nginx/      templates de configuração do nginx (produção)
docker-compose*.yml, .env.example
```

## Stack — backend (`backend/`)
- Python 3.12 + **FastAPI**, servido por Uvicorn
- **SQLAlchemy 2** (ORM, estilo tipado `Mapped[]`) + **Alembic** (migrations)
- **Pydantic v2** para schemas de entrada/saída; `pydantic-settings` para configuração
- Banco: **PostgreSQL 16** (container); backup diário com `pg_dump` (volume + rotação)
- Autenticação: usuário único, senha com hash **argon2**, sessão via **JWT em cookie
  `httpOnly` + `Secure` + `SameSite=Strict`**; rate limit no login
- E-mail: `aiosmtplib` (ver seção E-mail)
- Fila de envios: tabela no banco consumida por um **worker** próprio (mesmo código,
  outro processo/container); sem Redis, a menos que se mostre necessário
- OpenAPI gerado pelo FastAPI é o contrato com o front-end
- Testes: pytest + httpx (`AsyncClient`) contra banco PostgreSQL de teste
- Lint/format: ruff; tipos: mypy (modo estrito em `services/`)

### Organização do backend
```
app/
  api/        rotas (finas: validam, chamam services, retornam schemas)
  services/   regras de negócio (funções puras, sem FastAPI/HTTP)
  models/     modelos SQLAlchemy
  schemas/    modelos Pydantic
  core/       config, segurança, banco
  worker/     consumidor da fila de e-mails
```

## Stack — frontend (`frontend/`)
- **Vue 3** (Composition API, `<script setup>`) + **TypeScript** + **Vite**
- Vue Router; estado com **Pinia**
- Interface: **Padrão Digital de Governo (GovBR-DS)** — ver seção própria; mobile-first
- Cliente da API gerado a partir do OpenAPI (`openapi-typescript`) — não escrever
  tipos de API à mão
- **PWA** com `vite-plugin-pwa` (Workbox): instalável no celular e no computador
- **Chamada offline**: marcações salvas em IndexedDB (Dexie) e sincronizadas quando a
  conexão voltar; endpoint de sincronização idempotente (id gerado no cliente)
- Testes: Vitest (unitários) + Playwright (fluxos principais: login, chamada, notas)
- Lint/format: ESLint + Prettier

## Design System — GovBR-DS (https://www.gov.br/ds)
Toda a interface segue o **Padrão Digital de Governo**. Não usar outra biblioteca de
componentes (PrimeVue, Vuetify, Bootstrap, Tailwind etc.).

- Pacote: **`@govbr-ds/core`** (v3.x) — CSS, tokens e comportamentos JS dos componentes.
  Importar `@govbr-ds/core/dist/core.min.css` uma única vez em `main.ts`.
- **Componentes Vue próprios** em `frontend/src/components/govbr/`, prefixo `Br`
  (`BrButton`, `BrInput`, `BrSelect`, `BrTable`, `BrMessage`, `BrModal`, `BrHeader`,
  `BrMenu`, `BrBreadcrumb`, `BrCheckbox`, `BrRadio`, `BrDateTimePicker`, `BrLoading`...).
  Cada um renderiza exatamente a marcação/classes documentadas no GovBR-DS
  (`br-button`, `br-input`, `br-table`...) e expõe `v-model`, props e eventos Vue.
  - As views usam **somente** esses componentes, nunca a marcação crua do DS.
  - Quando o componente do DS depende do JS do core (menu, modal, select, tooltip...),
    instanciar a classe correspondente no `onMounted` e destruir no `onBeforeUnmount`.
  - Não usar `@govbr-ds/webcomponents`: o `v-model` com custom elements é frágil
    e dificulta a tipagem.
- **Tokens**: cores, espaçamentos, tipografia e sombras vêm das variáveis CSS do DS
  (`--blue-warm-vivid-70`, `--spacing-scale-2x`, `--font-size-scale-up-01` etc.).
  Não usar cores ou medidas fixas no CSS dos componentes.
- **Tipografia**: fonte **Rawline**, auto-hospedada em `frontend/public/fonts/`
  (sem CDN externo: funciona offline na PWA e não expõe acessos a terceiros).
- **Ícones**: Font Awesome 5 Free (`@fortawesome/fontawesome-free`), padrão do DS,
  com `aria-hidden="true"` quando decorativos.
- **Grid e layout**: grid do DS (`container-lg`, `row`, `col-*`) e o template de
  página gov.br (cabeçalho compacto, menu lateral, área de conteúdo).
- **Acessibilidade (obrigatória)**: seguir eMAG/WCAG 2.1 AA conforme as diretrizes do
  DS — `label` em todo campo, mensagens de erro associadas (`aria-describedby`), foco
  visível, navegação por teclado, contraste mínimo e textos alternativos.
- **Densidade**: na tela de chamada usar a densidade alta do DS (`small`), para caber
  a turma inteira no celular; nas demais, a densidade padrão.
- **Tema escuro**: usar as classes `dark-mode` do DS só nos componentes que as
  suportam; não inventar paleta própria.
- A marca do governo federal (logo gov.br) **não** é usada: o sistema é pessoal do
  professor, não um serviço oficial. Usar o nome e o ícone "Bizo Sala".

## Docker
- `docker-compose.yml` (base) + `docker-compose.dev.yml` (dev) + `docker-compose.prod.yml` (prod).
  Usar sempre esta nomenclatura (`docker-compose.<ambiente>.yml`).
- Serviços: `db` (PostgreSQL), `api` (FastAPI), `worker` (fila de e-mail),
  `web` (front-end), `mailpit` (só dev), `nginx` (só prod), `cloudflared` (prod, opcional).
- **Dev**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` — código montado em
  volume; `uvicorn --reload` na API e Vite dev server com HMR no front (proxy `/api`
  para a API); e-mails capturados pelo **Mailpit** (nunca enviar e-mail real em dev).
- **Prod**: publicado em **https://sala.bizo.dev.br** via **Cloudflare Tunnel**. O HTTPS
  termina na Cloudflare; nenhuma porta pública é aberta no VPS. O **nginx** (HTTP,
  `127.0.0.1:8080`) serve o build estático do Vue e faz proxy de `/api` para o Uvicorn.
  IP real do visitante vem do cabeçalho `CF-Connecting-IP`. Configuração em
  `nginx/*.template`. Mesma origem para front e API (sem CORS).
  `alembic upgrade head` roda no deploy.
- Configuração somente via variáveis de ambiente (`.env`, nunca versionado;
  manter `.env.example` atualizado).

## Modelo de domínio
- **Curso**: nível (`EMI` | `GRADUACAO`), regime (`ANUAL` | `SEMESTRAL`),
  parâmetros de avaliação (média de aprovação, possui exame final, regra de alerta de faltas)
- **PeriodoLetivo**: ano, semestre (opcional), datas de início/fim, ciclos avaliativos
  (EMI: 3 trimestres com datas; graduação: 1 ciclo)
- **DiaNaoLetivo**: data, descrição (feriados, recessos — afeta a projeção de carga horária)
- **Turma/Disciplina**: curso, período, carga horária total (h), dias da semana e
  nº de aulas (períodos de 50 min) em cada dia
- **Estudante**: nome, matrícula, e-mail, data de nascimento (menoridade), ativo;
  e-mail do responsável (EMI, opcional)
- **Aula** (encontro): turma, data, nº de horas-aula, status
  (`PREVISTA` | `DADA` | `CANCELADA`), origem (`GRADE` | `EXTRA`), motivo do cancelamento.
  Pode haver mais de uma aula no mesmo dia (aulas extras).
- **Frequencia**: estudante × aula → nº de faltas de 0 a N horas-aula da aula
  (OD art. 225; ex.: chegou atrasado numa aula dupla = 1 falta)
- **RegistroConteudo**: turma, data_inicio, data_fim, texto curto (cobre 1+ dias de aula)
- **Avaliacao**: turma, ciclo, nome, data, peso, tipo (`REGULAR` | `RECUPERACAO` | `EXAME`),
  avaliação(ões) que a recuperação substitui (ou o ciclo inteiro)
- **Substituicao**: estudante × avaliação de recuperação × avaliação substituída
  (escolha individual na reavaliação da graduação)
- **Nota**: estudante × avaliação (0 a 10, uma casa decimal — OD art. 206)
- **RecuperacaoParalela** (EMI): turma, ciclo, encontros de estudo, frequência dos
  estudantes nesses encontros, estudantes convocados/voluntários
- **AlertaFrequencia**: estudante, turma, aulas que dispararam, status
  (`PENDENTE` | `AVISADO`), data do aviso ao SISAE
- **Mensagem**: remetente, destinatários (estudantes ou turma), assunto, corpo,
  status por destinatário (`PENDENTE` | `ENVIADO` | `ERRO`), data

## Regras de negócio (fonte da verdade — cobrir com testes)

### Carga horária
1. Hora-aula = **50 min**. Horas cumpridas = Σ horas-aula das aulas `DADA` × 50 ÷ 60.
   60 h = 72 horas-aula; 120 h = 144 horas-aula.
2. Painel da turma: previsto × dado × saldo e **projeção** até o fim do período
   (calendário da turma − dias não letivos − cancelamentos). Alertar se não fechar.
3. Aulas `CANCELADA` não contam carga horária e não têm chamada (cancelar descarta a chamada).
3a. O calendário é gerado pelos horários da turma em todo o período, pulando dias não
    letivos; gerar de novo só cria o que falta. Aulas passadas **ficam em aberto**
    (`PREVISTA`) até a chamada ser feita — nunca marcar presença/falta automaticamente.
3b. Chamada offline: marcações em IndexedDB (Dexie) e envio idempotente
    (`PUT /aulas/{id}/chamada` substitui a chamada inteira).

### Frequência e alerta ao SISAE
4. Alerta (somente EMI): estudante com falta em **2 encontros (dias) consecutivos**
   da mesma turma gera `AlertaFrequencia` pendente. Um alerta por sequência; não duplicar.
   Falta no encontro = faltou **todas** as horas-aula do dia; atraso (falta parcial)
   não conta. Dias sem registro do estudante são ignorados.
   - Regra do professor/campus; a OD (art. 228) exige no mínimo o aviso após
     3 aulas consecutivas ou 5 alternadas para menores. Limites configuráveis no curso
     (`alerta_faltas_consecutivas`, `alerta_faltas_alternadas`); alternadas gera um
     alerta a cada N dias de falta no total.
   - Alertas são recalculados a cada chamada salva, aula cancelada/editada/excluída e
     mudança de limites no curso. Pendentes que deixam de valer são removidos;
     `AVISADO`/`DESCARTADO` ficam como histórico.
5. Graduação **não** gera alerta ao SISAE.
6. Frequência mínima para aprovação: **75%** (OD art. 224). Exibir % por estudante e
   destacar quem está em risco.

### Registro de conteúdo
7. Tela própria (separada da chamada), com um campo por dia de aula do período inteiro;
   o professor junta dias vizinhos num só registro ou os separa. Um registro cobre um
   intervalo de datas, inclusive futuras (planejamento do ano). Salvar substitui todos os
   registros da turma (`PUT /turmas/{id}/conteudos`).

### Notas
8. Nota do ciclo = Σ(nota × peso) ÷ Σ(pesos), arredondada a uma casa decimal (ROUND_HALF_UP).
   Avaliações sem nenhuma nota lançada na turma são ignoradas; numa avaliação já lançada,
   estudante sem nota conta 0. Cálculo puro em `services/notas.py` (testar lá).
   Mínimo de 2 avaliações por ciclo no EMI (OD art. 209, parágrafo único) — avisar, não bloquear.
8a. Recuperação (`Avaliacao.tipo = RECUPERACAO`) substitui, quando maior: `CICLO` (nota do
    trimestre — padrão EMI), `AVALIACAO` (uma avaliação fixa) ou `MELHOR` (a que mais aumenta
    a média — padrão graduação; o professor pode fixar outra por estudante em
    `Nota.substitui_avaliacao_id`).
9. Média parcial = média aritmética das notas dos ciclos (OD art. 217).
10. Aprovação (parametrizável por curso/PPC):
    - EMI: média ≥ **6,0** (OD art. 218 §1º), sem exame final.
    - Graduação (PPC atual **sem exame final**): média ≥ **6,0** (OD art. 218, II).
    - Manter suporte opcional a exame final (média ≥ 7,0 aprova; senão
      (média + exame) ÷ 2 ≥ 5,0 — OD arts. 218-219), desativado por padrão.

### Reavaliação na graduação (OD arts. 210, 212, 214, 220)
11a. Ao final do semestre, o estudante com média abaixo de 6,0 pode fazer uma
     **Reavaliação** (avaliação tipo `RECUPERACAO`, ciclo único).
11b. O professor **escolhe qual avaliação** a reavaliação substitui (uma por estudante,
     podendo variar entre estudantes). O sistema sugere a que mais eleva a média.
11c. A nota da reavaliação só substitui **quando maior** (art. 212 §2º).
11d. Sem direito à reavaliação o estudante que faltou sem justificativa a **todas**
     as avaliações do ciclo (art. 214, II) — avisar, permitindo sobrescrever.
11e. Quem fizer a reavaliação e continuar abaixo da média está reprovado (art. 220).
11f. A aula usada para a reavaliação é `CANCELADA` (motivo "Reavaliação") e não conta
     carga horária.

### Recuperação paralela (EMI — OD arts. 212, 236–248)
11. Obrigatória no EMI. Convocar estudantes com nota abaixo de **6,0** no ciclo (art. 245);
    voluntários com nota ≥ 6,0 podem participar mediante manifestação prévia (art. 247).
12. Só faz a reavaliação quem participou de **≥ 75%** dos encontros de recuperação (art. 246).
    **Pendente:** registrar encontros e frequência da recuperação; hoje a tela só informa a regra.
13. A nota da recuperação, **quando maior, substitui** a nota da avaliação ou do ciclo,
    conforme registrado no diário (art. 245, parágrafo único; art. 212 §2º).
14. A carga horária de recuperação deve ser de **10% a 20%** da carga horária executada no
    trimestre (art. 242) — calcular e exibir a faixa.
15. O tempo de recuperação **não conta** na carga horária da disciplina (art. 238 §1º).
    Quando um encontro for usado para recuperação, ele vira `CANCELADA`
    (motivo "Recuperação paralela") e o impacto na projeção de horas deve ser mostrado.
16. Etapas (art. 243): informar estudantes/responsáveis (e-mail), plano de estudos,
    dúvidas, reavaliação. Registro próprio de frequência/conteúdo/notas (art. 248).

### Exportação
17. Exportar chamada, conteúdo e notas em CSV/planilha para lançar no sistema acadêmico oficial.

## E-mail (Google Workspace @ifc.edu.br)
- Mensagem individual, para vários estudantes ou para a turma inteira; opção de
  copiar os responsáveis (EMI). Modelos prontos (convocação de recuperação, aviso de faltas).
- **Um e-mail por destinatário** (nunca expor a lista; no máximo BCC).
- Transporte: SMTP `smtp.gmail.com:587` (STARTTLS) com **senha de app** da conta
  `@ifc.edu.br` (variáveis `SMTP_USER` / `SMTP_PASSWORD`), enviado pelo worker com
  `aiosmtplib`. Sem OAuth.
- Respeitar limites do Workspace (~2.000 envios/dia): enviar por fila, com
  throttling e nova tentativa automática. Registrar status em `Mensagem`.
- Dev: sempre Mailpit.

## Convenções
- Regras de negócio em `backend/app/services/` (funções puras e testáveis); nunca nas
  rotas nem no front-end. O front apenas exibe o que a API calcula (médias, carga
  horária, alertas).
- Datas trafegam em ISO 8601; fuso `America/Sao_Paulo`; formato brasileiro só na interface.
- Notas como `Decimal` no backend (`NUMERIC(4,1)` no banco), nunca `float`.
- Segredos só em variáveis de ambiente. Migrations Alembic versionadas; não editar
  migrations aplicadas.
- Após mudar a API: regenerar o cliente TypeScript do front.
- Antes de concluir uma tarefa (dentro dos containers):
  backend `ruff check`, `ruff format --check`, `mypy`, `pytest`;
  frontend `npm run lint`, `npm run type-check`, `npm run test`.

## Prioridade de entrega (MVP)
1. Docker dev/prod, esqueleto FastAPI + Vue, autenticação, PWA básica
   - Componentes `Br*` já existentes: BrButton, BrInput, BrSelect, BrCheckbox, BrMessage,
     BrCard, BrHeader, BrModal, BrTable. Criar os demais conforme as telas precisarem.
   - Datas usam `BrInput type="date"` (nativo, bom no celular) em vez do datetimepicker
     do DS, que depende de flatpickr.
2. Telas de cadastro (CRUD) de cursos, períodos, dias não letivos, turmas e estudantes
   (importação via CSV) — não há painel admin pronto, então o CRUD faz parte do MVP
3. Calendário de aulas, chamada (celular) e carga horária
4. Alertas ao SISAE
5. Registro de conteúdo
6. Avaliações, notas e recuperação paralela
7. Envio de e-mails
8. Exportações
