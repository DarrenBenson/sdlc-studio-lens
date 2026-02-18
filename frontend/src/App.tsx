import { Route, Routes } from "react-router";

import { Layout } from "./components/Layout.tsx";
import { Dashboard } from "./pages/Dashboard.tsx";
import { DocumentList } from "./pages/DocumentList.tsx";
import { DocumentTree } from "./pages/DocumentTree.tsx";
import { DocumentView } from "./pages/DocumentView.tsx";
import { ProjectDetail } from "./pages/ProjectDetail.tsx";
import { SearchResults } from "./pages/SearchResults.tsx";
import { Settings } from "./pages/Settings.tsx";

function Placeholder({ title }: { title: string }) {
  return (
    <div className="text-text-secondary">
      <h2 className="font-display text-xl font-semibold text-text-primary">
        {title}
      </h2>
      <p className="mt-2">Coming soon.</p>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="projects/:slug" element={<ProjectDetail />} />
        <Route path="projects/:slug/tree" element={<DocumentTree />} />
        <Route
          path="projects/:slug/documents"
          element={<DocumentList />}
        />
        <Route
          path="projects/:slug/documents/:type/:docId"
          element={<DocumentView />}
        />
        <Route path="search" element={<SearchResults />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Placeholder title="Not Found" />} />
      </Route>
    </Routes>
  );
}
