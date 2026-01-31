# CineVibe - Streaming Interface

Uma interface de streaming inspirada na Netflix/Disney+ com integração à API do TMDB.

![CineVibe Screenshot](screenshot.png)

## Funcionalidades

- Interface moderna e responsiva inspirada em Netflix/Disney+
- Navegação por categorias de filmes e séries
- Filtro por plataformas de streaming (Netflix, Disney+, HBO Max, Prime Video, Apple TV+, Paramount+)
- Modal de detalhes com trailers do YouTube
- Seção "Onde Assistir" com links diretos para streaming
- **Minha Lista** - salvamento local de favoritos (persistente)
- Lazy loading inteligente para otimizar performance
- Cache de API para reduzir chamadas ao TMDB
- Animações suaves com Framer Motion

## Tecnologias

- **React 18** + **Vite** - Framework e build tool
- **Framer Motion** - Animações fluidas
- **TMDB API** - Dados de filmes e séries
- **IndexedDB** - Banco de dados local para "Minha Lista"
- **Lucide React** - Ícones modernos
- **CSS3** - Estilização com variáveis e gradientes

## Como usar

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/cinevibe.git
cd cinevibe
```

### 2. Instale as dependências
```bash
npm install
```

### 3. Configure a API Key do TMDB

1. Crie uma conta gratuita em [https://www.themoviedb.org](https://www.themoviedb.org)
2. Obtenha sua API key em Settings > API
3. Substitua a chave em `src/hooks/useTMDB.js`:

```javascript
const API_KEY = 'sua-api-key-aqui';
```

### 4. Execute o projeto
```bash
npm run dev
```

5. Acesse: http://localhost:3000

## Estrutura do Projeto

```
src/
├── components/
│   └── HomePage.jsx          # Componente principal
├── hooks/
│   ├── useTMDB.js            # Integração com TMDB API
│   └── useDatabase.js        # Hooks para IndexedDB
├── db/
│   └── index.js              # Configuração do banco local
├── styles/
│   └── HomePage.css          # Estilos globais
├── App.jsx
└── main.jsx
```

## Funcionalidades Detalhadas

### Lazy Loading
As linhas de filmes só carregam quando entram na viewport, economizando recursos.

### Cache Inteligente
Resultados da API são cacheados por 1 hora no IndexedDB.

### Minha Lista
- Clique no coração para adicionar/remover filmes
- Persiste entre sessões
- Mostra no topo da página inicial

### Onde Assistir
Mostra provedores de streaming disponíveis no Brasil com links diretos.

## Scripts Disponíveis

- `npm run dev` - Servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm run preview` - Preview do build

## Contribuição

Sinta-se à vontade para abrir issues e pull requests!

## Licença

MIT © 2024 CineVibe
