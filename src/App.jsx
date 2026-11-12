
import './App.css'

function App() {
  return (
    <div className="app">

      <aside className="sidebar">
        <div className="logo">
          <span className="logo-icon">Z</span>
          <h2>ZOE</h2>
        </div>

        <button className="new-chat">
          + Nova conversa
        </button>

        <div className="menu">
          <p className="menu-title">MENU</p>
          <button>⌂ Início</button>
          <button>◷ Histórico</button>
          <button>⚙ Configurações</button>
        </div>

        <div className="sidebar-bottom">
          <span className="status-dot"></span>
          Sistema local ativo
        </div>
      </aside>

      <main className="main">

        <header className="topbar">
          <span>ASSISTENTE PESSOAL</span>
          <span className="online">
            ● ONLINE
          </span>
        </header>

        <section className="welcome">
          <div className="avatar">
            Z
          </div>

          <h1>Olá, sou a <span>ZOE.</span></h1>

          <p>
            Sua assistente pessoal inteligente.
            Estou pronta para ajudar.
          </p>

          <div className="suggestions">
            <button>Como você pode me ajudar?</button>
            <button>Quero programar</button>
            <button>Organizar minhas tarefas</button>
          </div>
        </section>

        <footer className="chat-area">
          <div className="input-container">
            <input
              type="text"
              placeholder="Converse com a ZOE..."
            />
            <button className="send-button">
              ↑
            </button>
          </div>

          <p>Processamento local • Privacidade em primeiro lugar</p>
        </footer>

      </main>
    </div>
  )
}

export default App
