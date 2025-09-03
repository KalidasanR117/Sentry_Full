import { SentryDashboard } from "@/components/SentryDashboard";

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-black text-gray-100">
      {/* Header */}
      <header className="w-full bg-gray-900/80 backdrop-blur-md shadow-md p-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Sentry AI</h1>
        <nav>
          <ul className="flex space-x-4 text-sm">
            <li className="hover:text-blue-400 cursor-pointer">Dashboard</li>
            <li className="hover:text-blue-400 cursor-pointer">Reports</li>
            <li className="hover:text-blue-400 cursor-pointer">Settings</li>
          </ul>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6">
        <SentryDashboard />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900/80 backdrop-blur-md text-center text-sm py-3 border-t border-gray-700 text-gray-400">
        © {new Date().getFullYear()} Sentry AI — All rights reserved
      </footer>
    </div>
  );
};

export default Index;
