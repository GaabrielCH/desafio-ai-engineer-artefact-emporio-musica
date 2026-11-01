# Exemplo 4 — Informações Gerais da Loja, Horário de Funcionamento e Cálculo de Frete

> **Cenário demonstrado:** Cliente solicita endereço, horário de funcionamento, contatos de WhatsApp e consulta regras e custos de entrega para Campo Grande/MS (motoboy próprio / frete grátis acima de R$ 500) e Dourados/MS (PAC, SEDEX e Jadlog — Seção 5).
> **Data de referência do sistema:** `2026-03-23`

---

## Turno 1

### 👤 Cliente
> Qual o endereço da loja, telefone de contato e o horário de funcionamento durante a semana e no sábado?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (1 call)</b></summary>

- **`consultar_politicas_loja({"pergunta": "endereço localização dados da empresa horário de funcionamento segunda a sábado domingo telefone whatsapp e-mail de contato"})`**

</details>

### 🤖 Agente (Empório da Música)

Olá! Tudo bem? Bem-vindo(a) à **Empório da Música**! 🎸

### 📍 Informações da Loja — Empório da Música
- **Endereço:** Rua 14 de Maio, 3200 — Centro, Campo Grande – MS, CEP 79202-333
- **Horário de Funcionamento (Loja Física e WhatsApp):**
  - **Segunda a Sexta-feira:** 09:00 às 18:00
  - **Sábado:** 09:00 às 13:00
  - **Domingos e Feriados:** Fechado *(em datas especiais como Black Friday, Aniversário da Loja e Natal, o horário pode ser estendido)*
- **Canais de Contato:**
  - **WhatsApp Central de Atendimento:** `(67) 3321-4500`
  - **Telefone / WhatsApp Loja Física:** `(67) 3341-4444`
  - **E-mail:** `contato@emporiodamusica.com.br`
- **CNPJ:** 12.345.678/0001-90

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---

## Turno 2

### 👤 Cliente
> Quanto fica o frete para entregar um violão de R$ 600 aqui em Campo Grande? E se eu pedir para entregar na casa do meu primo em Dourados?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (2 calls)</b></summary>

- **`calcular_frete_e_entrega({"cidade": "Campo Grande", "valor_pedido_brl": 600.0, "instrumento_grande_porte": false})`**
- **`calcular_frete_e_entrega({"cidade": "Dourados", "valor_pedido_brl": 600.0, "instrumento_grande_porte": false})`**

</details>

### 🤖 Agente (Empório da Música)

### 🚚 Frete e Prazos de Entrega — Campo Grande
- **Região:** Região Metropolitana de Campo Grande/MS (Seção 5.1) | Peso/Cubagem estimada: `3.2 kg` (`106x46x16 cm (Padrão Violão)`)
- **Custo do Frete:** ✅ **GRÁTIS (R$ 0,00)** — pedido acima de R$ 500,00!
- **Prazo de entrega:** **1 a 3 dias úteis** via **motoboy próprio** (nossa equipe entra em contato por telefone antes da entrega).

---

### 🚚 Frete e Prazos de Entrega — Dourados
- **Região:** Interior de Mato Grosso do Sul (Seção 5.2) | Peso/Cubagem estimada: `3.2 kg` (`106x46x16 cm (Padrão Violão)`)
- **Cálculo do frete:** Calculado com base no CEP/região de destino, peso/cubagem do instrumento e seguro ad valorem (1,5%).
- **Modalidades, Valores e Prazos Estimados:**
  - **PAC (Correios):** 5 a 12 dias úteis — **R$ 55,10** *(Rastreamento + Seguro inclusos)*
  - **Jadlog (.package):** 3 a 8 dias úteis — **R$ 67,34** *(Rastreamento + Seguro inclusos)*
  - **SEDEX (Correios):** 2 a 5 dias úteis — **R$ 87,46** *(Rastreamento + Seguro inclusos)*
- *Nota: Baterias acústicas, pianos digitais e contrabaixos podem exigir cotação individual de frete.*

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---
