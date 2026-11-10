"""Dados fictícios: nomes, CPFs inválidos de propósito, restaurantes, cardápios e endereços.

Regra do projeto: nenhum dado pessoal real. Os CPFs têm o dígito verificador errado, então nunca
coincidem com um CPF de verdade. Os nomes de restaurantes e ruas são genéricos e inventados.
"""

from __future__ import annotations

import random

FIRST_NAMES = (
    "Rita",
    "Joana",
    "Carla",
    "Beatriz",
    "Lúcia",
    "Fernanda",
    "Patrícia",
    "Camila",
    "Aline",
    "Renata",
    "Marcos",
    "Rafael",
    "Bruno",
    "Diego",
    "Tiago",
    "Paulo",
    "Henrique",
    "Rodrigo",
    "Gustavo",
    "Eduardo",
    "Sônia",
    "Vera",
    "Cláudia",
    "Juliana",
    "Larissa",
    "André",
    "Fábio",
    "Leandro",
    "Otávio",
    "Murilo",
)
SURNAMES = (
    "Boaventura",
    "Quintela",
    "Arantes",
    "Valadares",
    "Sampaio",
    "Bragança",
    "Teixeira",
    "Albuquerque",
    "Mendonça",
    "Figueiredo",
    "Carvalhal",
    "Azevedo",
    "Monteiro",
    "Rezende",
    "Paranhos",
    "Lacerda",
    "Saldanha",
    "Brandão",
    "Coutinho",
    "Vasconcelos",
    "Guimarães",
    "Barreto",
    "Peixoto",
    "Damasceno",
)
STYLES = (
    "de forma direta e curta",
    "com algumas gírias e pouca pontuação, como no WhatsApp",
    "de forma educada e um pouco formal",
    "rápido, com um ou outro erro de digitação",
    "de forma simpática, mas objetiva",
)


def fake_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(SURNAMES)}"


def _check_digit(digits: list[int]) -> int:
    weight = len(digits) + 1
    total = sum(d * (weight - i) for i, d in enumerate(digits))
    rest = (total * 10) % 11
    return 0 if rest == 10 else rest


def is_valid_cpf(cpf: str) -> bool:
    """Algoritmo oficial do dígito verificador. Usado nos testes para garantir que nenhum CPF é válido."""
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    return _check_digit(d[:9]) == d[9] and _check_digit(d[:10]) == d[10]


def fake_cpf(rng: random.Random) -> str:
    """CPF com formato correto e primeiro dígito verificador errado de propósito."""
    base = [rng.randint(0, 9) for _ in range(9)]
    while len(set(base)) == 1:
        base = [rng.randint(0, 9) for _ in range(9)]
    right = _check_digit(base)
    wrong = (right + rng.randint(1, 9)) % 10
    second = rng.randint(0, 9)
    s = "".join(map(str, [*base, wrong, second]))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


#: Restaurantes fictícios e cardápios (item, preço, categoria).
RESTAURANTS: dict[str, list[tuple[str, float, str]]] = {
    "Cantina da Praça": [
        ("Combo smash burger", 42.90, "principal"),
        ("Cheeseburger duplo", 36.50, "principal"),
        ("Batata média", 14.00, "acompanhamento"),
        ("Onion rings", 18.90, "acompanhamento"),
        ("Refrigerante lata", 8.00, "bebida"),
        ("Milkshake de morango", 19.90, "sobremesa"),
    ],
    "Sabor de Minas": [
        ("Feijão tropeiro completo", 39.90, "principal"),
        ("Frango com quiabo", 37.50, "principal"),
        ("Pão de queijo (6 unidades)", 15.90, "acompanhamento"),
        ("Torresmo", 22.00, "acompanhamento"),
        ("Suco de laranja 500 ml", 11.00, "bebida"),
        ("Doce de leite com queijo", 14.50, "sobremesa"),
    ],
    "Sushi Maré": [
        ("Combinado 20 peças", 64.90, "principal"),
        ("Temaki de salmão", 32.90, "principal"),
        ("Hot roll (10 unidades)", 27.90, "acompanhamento"),
        ("Guioza (6 unidades)", 24.90, "acompanhamento"),
        ("Chá gelado", 9.90, "bebida"),
        ("Harumaki de banana", 16.90, "sobremesa"),
    ],
    "Pizzaria Forno Velho": [
        ("Pizza grande de calabresa", 58.90, "principal"),
        ("Pizza média marguerita", 44.90, "principal"),
        ("Pão de alho", 16.90, "acompanhamento"),
        ("Esfiha de carne (4 unidades)", 21.90, "acompanhamento"),
        ("Refrigerante 2 litros", 14.90, "bebida"),
        ("Pizza doce de chocolate", 39.90, "sobremesa"),
    ],
    "Marmitaria Dona Lu": [
        ("Marmita de bife acebolado", 31.90, "principal"),
        ("Marmita de frango grelhado", 28.90, "principal"),
        ("Porção de farofa", 9.90, "acompanhamento"),
        ("Salada de maionese", 12.90, "acompanhamento"),
        ("Suco de maracujá 500 ml", 10.00, "bebida"),
        ("Pudim de leite", 12.00, "sobremesa"),
    ],
    "Açaí da Orla": [
        ("Açaí 700 ml completo", 34.90, "principal"),
        ("Açaí 500 ml com granola", 26.90, "principal"),
        ("Tapioca de queijo", 17.90, "acompanhamento"),
        ("Crepe de frango", 23.90, "acompanhamento"),
        ("Água de coco", 9.00, "bebida"),
        ("Brownie", 13.90, "sobremesa"),
    ],
    "Temakeria Onda": [
        ("Temaki hot filadélfia", 34.90, "principal"),
        ("Yakisoba de carne", 41.90, "principal"),
        ("Sunomono", 12.90, "acompanhamento"),
        ("Shimeji na manteiga", 29.90, "acompanhamento"),
        ("Refrigerante lata", 7.50, "bebida"),
        ("Sorvete de gengibre", 15.90, "sobremesa"),
    ],
    "Pastelaria do Largo": [
        ("Pastel de carne com queijo", 16.90, "principal"),
        ("Pastel de palmito", 15.90, "principal"),
        ("Coxinha (4 unidades)", 19.90, "acompanhamento"),
        ("Kibe (4 unidades)", 18.90, "acompanhamento"),
        ("Caldo de cana 500 ml", 9.50, "bebida"),
        ("Pastel de banana com canela", 14.90, "sobremesa"),
    ],
}

STREETS = (
    "Rua das Acácias",
    "Avenida dos Ipês",
    "Rua Ouro Verde",
    "Rua do Mirante",
    "Travessa dos Coqueiros",
    "Rua Jardim das Flores",
    "Avenida Beira-Rio",
    "Rua Monte Alegre",
    "Rua dos Girassóis",
    "Rua Pedra Azul",
    "Alameda das Palmeiras",
    "Rua Vale do Sol",
    "Rua Campos Novos",
    "Avenida Primavera",
)
STATES = ("Bahia", "Pernambuco", "Paraná", "Goiás", "Pará", "Ceará", "Santa Catarina", "Amazonas")


def fake_address(rng: random.Random) -> str:
    number = rng.randint(10, 1999)
    complement = rng.choice(("", "", f", apto {rng.randint(11, 304)}", f", casa {rng.randint(1, 9)}"))
    return f"{rng.choice(STREETS)}, {number}{complement}"


def fake_pix_key(rng: random.Random, owner_first_name: str) -> str:
    kind = rng.choice(("email", "telefone"))
    if kind == "email":
        return f"{owner_first_name.lower()}.{rng.randint(10, 99)}@exemplo.com.br"
    return f"+55119{rng.randint(10000000, 99999999)}"
