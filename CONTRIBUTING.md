# 🤝 Guia de Contribuição

Obrigado pelo interesse em contribuir com o Voice Cloning SaaS! Este documento fornece diretrizes para contribuições.

## 📋 Como Contribuir

### 1. Fork e Clone

```bash
# Fork o repositório no GitHub
# Clone seu fork
git clone https://github.com/seu-usuario/voice-cloning-saas.git
cd voice-cloning-saas
```

### 2. Crie uma Branch

```bash
git checkout -b feature/minha-feature
# ou
git checkout -b fix/meu-bugfix
```

### 3. Configure o Ambiente

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. Faça suas Alterações

- Siga o estilo de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação se necessário

### 5. Commit suas Alterações

Use mensagens de commit descritivas:

```bash
git commit -m "feat: adiciona suporte a novo idioma"
git commit -m "fix: corrige erro no processamento de áudio"
git commit -m "docs: atualiza documentação da API"
```

**Prefixos recomendados:**
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação (sem mudança de código)
- `refactor:` - Refatoração
- `test:` - Testes
- `chore:` - Tarefas de manutenção

### 6. Push e Pull Request

```bash
git push origin feature/minha-feature
```

Abra um Pull Request no GitHub com:
- Descrição clara das mudanças
- Link para issue relacionada (se houver)
- Screenshots (se aplicável)

## 🧪 Testes

Antes de submeter, rode os testes:

```bash
pytest
```

## 📝 Estilo de Código

- **Python**: Siga PEP 8
- **JavaScript/React**: Use ESLint + Prettier
- Use type hints em Python
- Docstrings para funções públicas

## 🐛 Reportando Bugs

Ao reportar bugs, inclua:
- Descrição do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Versão do Python/sistema operacional
- Logs de erro (se houver)

## 💡 Sugerindo Features

Abra uma issue com:
- Descrição da feature
- Caso de uso
- Implementação sugerida (opcional)

## 📜 Código de Conduta

- Seja respeitoso e inclusivo
- Aceite feedback construtivo
- Foque no que é melhor para a comunidade

## ❓ Dúvidas?

Abra uma issue ou entre em contato com os maintainers.

---

Obrigado por contribuir! 🎉
