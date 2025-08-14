
function App() {
  return (
    <div className="min-h-screen bg-secondary-50">
      <header className="bg-white shadow-sm border-b border-secondary-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">
                FlowSketch
              </h1>
            </div>
            <nav className="flex space-x-4">
              <button className="btn-primary">New Project</button>
              <button className="btn-secondary">Sign In</button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-secondary-900 mb-4">
            Transform Ideas into Visual Diagrams
          </h2>
          <p className="text-xl text-secondary-600 mb-8 max-w-3xl mx-auto">
            FlowSketch uses AI to automatically convert unstructured text into
            synchronized diagrams and specifications. Paste your meeting notes,
            brainstorming docs, or requirements and watch them come to life.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="card">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-secondary-900 mb-2">
                AI-Powered Parsing
              </h3>
              <p className="text-secondary-600">
                Automatically extract entities, relationships, and workflows
                from unstructured text.
              </p>
            </div>

            <div className="card">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-secondary-900 mb-2">
                Interactive Diagrams
              </h3>
              <p className="text-secondary-600">
                Edit diagrams with smooth drag-and-drop interface and real-time
                synchronization.
              </p>
            </div>

            <div className="card">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2v0a2 2 0 01-2-2v-1"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-secondary-900 mb-2">
                Generated Specs
              </h3>
              <p className="text-secondary-600">
                Automatically generate comprehensive specifications with
                acceptance criteria and tests.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
