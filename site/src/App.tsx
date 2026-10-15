import { lazy, Suspense } from "react";
import { HashRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { LoadingState } from "./components/ui/StateViews";
import OverviewPage from "./pages/OverviewPage";

// Heavier pages load on demand (the playground pulls in the editor; the
// benchmark pulls in the chart library).
const PlaygroundPage = lazy(() => import("./pages/PlaygroundPage"));
const BenchmarkPage = lazy(() => import("./pages/BenchmarkPage"));
const ExplorerPage = lazy(() => import("./pages/ExplorerPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

// HashRouter: GitHub Pages serves static files only, so deep links use #/path.
export default function App() {
  return (
    <HashRouter>
      <AppShell>
        <Suspense fallback={<LoadingState />}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/playground" element={<PlaygroundPage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="/explorer" element={<ExplorerPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </AppShell>
    </HashRouter>
  );
}
