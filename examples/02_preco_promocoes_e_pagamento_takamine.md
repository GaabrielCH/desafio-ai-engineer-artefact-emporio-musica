# Exemplo 2 — Consulta de Preço, Promoções (Ativas vs Expiradas) e Regras de Pagamento

> **Cenário demonstrado:** Cliente consulta o preço do Takamine GD20 (R$ 2.199,00), verifica se uma promoção antiga ainda vale (Seção 7.3 — promoção expirada), simula pagamento no PIX (5%) e parcelamento sem juros (Seção 3.1), e pergunta quais violões/ukuleles estão em promoção ativa agora (Seção 6.2 — não cumulatividade do PIX).
> **Data de referência do sistema:** `2026-03-23`

---

## Turno 1

### 👤 Cliente
> Olá! Quanto custa o Takamine GD20? Como ficam as opções de pagamento no PIX e parcelado no cartão?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (1 call)</b></summary>

- **`detalhar_produto_e_pagamento({"nome_ou_id_produto": "takamine gd20"})`**

</details>

### 🤖 Agente (Empório da Música)

Olá! Tudo bem? Bem-vindo(a) à **Empório da Música**! 🎸

### 🎵 Takamine GD20 Dreadnought Natural (`ID #95`)
- **Categoria:** Violões
- **Descrição:** Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido.
- **Especificações técnicas:** top: `Cedro Sólido`, back_sides: `Sapele`, neck: `Mogno`, strings: `steel`, scale: `650mm`, electronics: `no`, color: `Natural`
- **Disponibilidade:** ✅ **Em estoque** (5 unidades disponíveis para pronta entrega)

#### 💰 Preço e Condições de Pagamento
- **Preço de Tabela:** **R$ 2.199,00**
- **À vista no PIX (5% de desconto):** **R$ 2.089,05** *(economia de R$ 109,95)*
- **Cartão de Débito ou Boleto Bancário:** R$ 2.199,00 à vista
- **Status de Promoções:** Verificando no sistema, a campanha anterior (*Oferta Especial (12%)*) **já está encerrada (`inativa`)**. O valor vigente hoje é o de tabela com os 5% de desconto para pagamento via PIX.
- **Cartão de Crédito sem juros:** **Até 12x de R$ 183,25 sem juros no cartão de crédito** (respeitando nossas faixas: até 3x com parcela mínima de R$ 50, 4x a 6x mín. R$ 80, e 7x a 12x mín. R$ 100).
- **Combinação de Pagamento:** ✅ Como o valor supera R$ 2.000,00, você também pode **combinar formas de pagamento** (por exemplo, dar uma entrada no PIX e parcelar o restante no cartão)!

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---

## Turno 2

### 👤 Cliente
> E quais instrumentos estão em promoção ativa hoje na loja? O desconto do PIX acumula com a promoção do Taylor 110e?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (3 calls)</b></summary>

- **`detalhar_produto_e_pagamento({"nome_ou_id_produto": "taylor 110e"})`**
- **`listar_promocoes({"incluir_expiradas": false})`**
- **`consultar_politicas_loja({"pergunta": "regras de promoções e descontos cumulatividade pix"})`**

</details>

### 🤖 Agente (Empório da Música)

### 🎵 Taylor 110e Dreadnought Natural (`ID #94`)
- **Categoria:** Violões
- **Descrição:** Violão dreadnought Taylor com tampo sólido em Sitka Spruce e eletrônica ES2. Perfeito para palco com som amplificado de alta fidelidade.
- **Especificações técnicas:** top: `Sitka Spruce Sólido`, back_sides: `Walnut`, neck: `Tropical Mahogany`, strings: `steel`, scale: `648mm`, electronics: `yes`, color: `Natural`
- **Disponibilidade:** ✅ **Em estoque** (4 unidades disponíveis para pronta entrega)

#### 🔥 Promoção Ativa (Desconto Exclusivo — 8% de desconto!)
- **Preço Original de Tabela:** ~~R$ 5.999,00~~
- **Preço Promocional Vigente:** **R$ 5.519,08**
- *(Nota sobre cumulatividade — Seção 6.2: como este instrumento já está com 8% de desconto promocional, o desconto de 5% do PIX não é cumulativo, mantendo-se **R$ 5.519,08** no PIX).*
- **Cartão de Crédito sem juros:** **Até 12x de R$ 459,92 sem juros no cartão de crédito** (respeitando nossas faixas: até 3x com parcela mínima de R$ 50, 4x a 6x mín. R$ 80, e 7x a 12x mín. R$ 100).
- **Combinação de Pagamento:** ✅ Como o valor supera R$ 2.000,00, você também pode **combinar formas de pagamento** (por exemplo, dar uma entrada no PIX e parcelar o restante no cartão)!

---

### 🔥 Promoções Ativas no Sistema Agora (4 ofertas vigentes):
- **Ohana CK-20 Concert Natural** (Ukuleles) — Campanha *Desconto Exclusivo*:
  De ~~R$ 549,00~~ por **R$ 439,20** (**20% OFF!**) — *6 un. em estoque*
- **Crafter HT-100 Folk Aço Natural** (Violões) — Campanha *Desconto Exclusivo*:
  De ~~R$ 2.399,00~~ por **R$ 1.967,18** (**18% OFF!**) — *3 un. em estoque*
- **Kalani KAL-700T Tenor Natural** (Ukuleles) — Campanha *Oferta Especial*:
  De ~~R$ 359,00~~ por **R$ 323,10** (**10% OFF!**) — *11 un. em estoque*
- **Taylor 110e Dreadnought Natural** (Violões) — Campanha *Desconto Exclusivo*:
  De ~~R$ 5.999,00~~ por **R$ 5.519,08** (**8% OFF!**) — *4 un. em estoque*

> 📌 **Regras de Promoções (Seção 6.2 do Manual):**
> - Promoções **não são cumulativas**: o desconto de 5% do PIX não se aplica sobre preços já promocionais.
> - Ofertas válidas enquanto durar o estoque (sem reserva de preço / *rain check*).

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---
