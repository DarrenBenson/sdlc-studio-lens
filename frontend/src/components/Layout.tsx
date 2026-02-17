import { Outlet } from "react-router";

import { SearchBar } from "./SearchBar.tsx";
import { Sidebar } from "./Sidebar.tsx";

export function Layout() {
  return (
    <div className="flex h-screen bg-bg-base">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center border-b border-border-default px-6 py-3">
          <SearchBar />
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
