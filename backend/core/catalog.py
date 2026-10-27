"""Catálogo demonstrativo: valores e respostas pertencem sempre ao servidor."""

CHALLENGES = [
    {
        "id": "energia",
        "title": "Energia em movimento",
        "category": "Sustentabilidade",
        "points": 80,
        "question": "Qual destas fontes de energia é renovável?",
        "options": ["Carvão", "Vento", "Petróleo"],
        "answer": 1,
        "explanation": "O vento é um recurso renovável e pode ser convertido em eletricidade.",
    },
    {
        "id": "mecanica",
        "title": "O essencial da mecânica",
        "category": "Engenharia",
        "points": 100,
        "question": "Qual é a unidade de força no Sistema Internacional?",
        "options": ["Watt", "Joule", "Newton"],
        "answer": 2,
        "explanation": "O newton mede força; o joule mede energia e o watt mede potência.",
    },
    {
        "id": "circular",
        "title": "Dar uma nova volta",
        "category": "Economia circular",
        "points": 120,
        "question": "Que ação prolonga a vida útil de uma máquina?",
        "options": ["Manutenção preventiva", "Ignorar desgaste", "Eliminar inspeções"],
        "answer": 0,
        "explanation": "A manutenção preventiva ajuda a detetar desgaste antes de uma avaria.",
    },
]
REWARDS = [
    {
        "id": "autocolantes",
        "title": "Pack de autocolantes",
        "description": "Um toque de engenharia no teu portátil.",
        "cost": 80,
        "icon": "✳",
    },
    {
        "id": "caderno",
        "title": "Caderno de ideias",
        "description": "Para os projetos que ainda estão por nascer.",
        "cost": 180,
        "icon": "▤",
    },
    {
        "id": "garrafa",
        "title": "Garrafa reutilizável",
        "description": "Mais água. Menos descartáveis.",
        "cost": 250,
        "icon": "◉",
    },
]
