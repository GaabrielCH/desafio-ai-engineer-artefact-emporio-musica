# Exemplo 1 — Consulta ao Catálogo de Produtos e Tratamento de Indisponibilidade

> **Cenário demonstrado:** Cliente busca violões disponíveis até R$ 1.000,00 e, em seguida, pergunta especificamente sobre o Giannini GF-3D (que custa R$ 799,90 mas está com estoque zero) e o Shelby SN-7C (descontinuado), demonstrando a aplicação rigorosa da Seção 7.3 do Manual.
> **Data de referência do sistema:** `2026-03-23`

---

## Turno 1

### 👤 Cliente
> Oi, meu nome é Lucas! Quais opções de violões disponíveis custando até R$1000?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (1 call)</b></summary>

- **`buscar_produtos({"termo_busca": null, "categoria": "Violões", "preco_max": 1000.0, "preco_min": null, "tipo_corda": null, "eletrico": null, "apenas_disponiveis": true})`**

</details>

### 🤖 Agente (Empório da Música)

Olá, Lucas! Tudo bem? 🎸

Consultei nosso catálogo em tempo real! Encontrei **12 opções de violões disponíveis em estoque** até **R$ 1.000,00**:

**Cordas de Nylon** *(mais macias, ideais para iniciantes, clássico, MPB e choro)*:
- **Tagima Memphis AC-39 Nylon Natural**: **R$ 429,90** (ou **R$ 408,40** à vista no PIX | Até 5x de R$ 85,98 sem juros no cartão de crédito) — *15 un. em estoque*
- **Rozini RC-104 Nylon Estudante**: **R$ 459,90** (ou **R$ 436,90** à vista no PIX | Até 5x de R$ 91,98 sem juros no cartão de crédito) — *10 un. em estoque*
- **Yamaha C40 Nylon Natural**: **R$ 599,90** (ou **R$ 569,90** à vista no PIX | Até 6x de R$ 99,98 sem juros no cartão de crédito) — *12 un. em estoque*
- **Giannini GN-15 Nylon Cedr Natural**: **R$ 689,00** (ou **R$ 654,55** à vista no PIX | Até 6x de R$ 114,83 sem juros no cartão de crédito) — *6 un. em estoque*
- **Yamaha C70 Nylon Natural**: **R$ 849,00** (ou **R$ 806,55** à vista no PIX | Até 8x de R$ 106,12 sem juros no cartão de crédito) — *8 un. em estoque*

**Cordas de Aço** *(som mais brilhante e encorpado, ótimo para pop, folk, rock e sertanejo)*:
- **Shelby SN-100 Folk Aço Preto**: **R$ 549,00** (ou **R$ 521,55** à vista no PIX | Até 6x de R$ 91,50 sem juros no cartão de crédito) — *5 un. em estoque*
- **Giannini GF-1R Aço Folk Sunburst**: **R$ 579,90** (ou **R$ 550,90** à vista no PIX | Até 6x de R$ 96,65 sem juros no cartão de crédito) — *7 un. em estoque*
- **Yamaha F310 Aço Natural**: **R$ 699,90** (ou **R$ 664,90** à vista no PIX | Até 6x de R$ 116,65 sem juros no cartão de crédito) — *14 un. em estoque*
- **Tagima Dallas Tuner Aço Natural**: **R$ 749,00** (ou **R$ 711,55** à vista no PIX | Até 7x de R$ 107,00 sem juros no cartão de crédito) — *9 un. em estoque*
- **Shelby SGD-195E Elétrico Aço Sunburst**: **R$ 799,00** (ou **R$ 759,05** à vista no PIX | Até 7x de R$ 114,14 sem juros no cartão de crédito) | Eletroacústico — *6 un. em estoque*
- **Tagima Woodstock Dreadnought Natural**: **R$ 899,00** (ou **R$ 854,05** à vista no PIX | Até 8x de R$ 112,38 sem juros no cartão de crédito) — *11 un. em estoque*
- **Tagima TW-7 7 Cordas Aço Natural**: **R$ 999,00** (ou **R$ 949,05** à vista no PIX | Até 9x de R$ 111,00 sem juros no cartão de crédito) — *6 un. em estoque*

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---

## Turno 2

### 👤 Cliente
> Eu vi em um anúncio antigo o violão Giannini GF-3D e o Shelby SN-7C de 7 cordas. Vocês têm eles em estoque?

<details>
<summary>🛠️ <b>Ferramentas acionadas pelo Agente (2 calls)</b></summary>

- **`detalhar_produto_e_pagamento({"nome_ou_id_produto": "giannini gf-3d"})`**
- **`detalhar_produto_e_pagamento({"nome_ou_id_produto": "shelby sn-7c"})`**

</details>

### 🤖 Agente (Empório da Música)

Claro, Lucas!

### 🎵 Giannini GF-3D Dreadnought Sunburst (`ID #96`)
- **Categoria:** Violões
- **Descrição:** Violão dreadnought com corpo amplo e acabamento Sunburst. Volume alto e graves profundos, ideal para country e pop.
- **Especificações técnicas:** top: `Spruce`, back_sides: `Sapele`, neck: `Nato`, strings: `steel`, scale: `650mm`, electronics: `no`, color: `Sunburst`
- **Disponibilidade:** ⚠️ **Temporariamente Fora de Estoque (0 unidades)**.
  *Seguindo nossa política de transparência, nunca confirmamos venda de item sem estoque físico.*

#### 💰 Preço e Condições de Pagamento
- **Preço de Tabela:** **R$ 799,90**
- **À vista no PIX (5% de desconto):** **R$ 759,90** *(economia de R$ 40,00)*
- **Cartão de Débito ou Boleto Bancário:** R$ 799,90 à vista
- **Status de Promoções:** Verificando no sistema, a campanha anterior (*Semana do Músico (40%), Semana do Músico (18%)*) **já está encerrada (`inativa`)**. O valor vigente hoje é o de tabela com os 5% de desconto para pagamento via PIX.
- **Cartão de Crédito sem juros:** **Até 7x de R$ 114,27 sem juros no cartão de crédito** (respeitando nossas faixas: até 3x com parcela mínima de R$ 50, 4x a 6x mín. R$ 80, e 7x a 12x mín. R$ 100).

#### 💡 Alternativas equivalentes disponíveis para pronta entrega:
- **Shelby SGD-195E Elétrico Aço Sunburst** — **R$ 799,00** (*6 un. em estoque*)
- **Yamaha C70 Nylon Natural** — **R$ 849,00** (*8 un. em estoque*)
- **Tagima Dallas Tuner Aço Natural** — **R$ 749,00** (*9 un. em estoque*)

---

### 🎵 Shelby SN-7C 7 Cordas Nylon Natural (`ID #113`)
- **Categoria:** Violões
- **Descrição:** Violão 7 cordas clássico com acabamento natural e braço em cedro. Boa opção para estudantes de choro que buscam qualidade acessível.
- **Especificações técnicas:** top: `Linden`, back_sides: `Linden`, neck: `Cedro`, strings: `nylon`, scale: `650mm`, electronics: `no`, color: `Natural`
- **Disponibilidade:** 🚫 **Produto Descontinuado** (não faz mais parte do catálogo ativo da loja).

#### 💰 Preço e Condições de Pagamento
- **Preço de Tabela:** **R$ 749,00**
- **À vista no PIX (5% de desconto):** **R$ 711,55** *(economia de R$ 37,45)*
- **Cartão de Débito ou Boleto Bancário:** R$ 749,00 à vista
- **Status de Promoções:** Verificando no sistema, a campanha anterior (*Black Friday (25%)*) **já está encerrada (`inativa`)**. O valor vigente hoje é o de tabela com os 5% de desconto para pagamento via PIX.
- **Cartão de Crédito sem juros:** **Até 7x de R$ 107,00 sem juros no cartão de crédito** (respeitando nossas faixas: até 3x com parcela mínima de R$ 50, 4x a 6x mín. R$ 80, e 7x a 12x mín. R$ 100).

#### 💡 Alternativas equivalentes disponíveis para pronta entrega:
- **Tagima Dallas Tuner Aço Natural** — **R$ 749,00** (*9 un. em estoque*)
- **Yamaha F310 Aço Natural** — **R$ 699,90** (*14 un. em estoque*)
- **Shelby SGD-195E Elétrico Aço Sunburst** — **R$ 799,00** (*6 un. em estoque*)

Ficou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊

---
