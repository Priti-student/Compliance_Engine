import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import LoginPage from "./auth/LoginPage";
import Shell from "./layout/Shell";
import DashboardPage from "./pages/DashboardPage";
import ProductsPage from "./pages/ProductsPage";
import RepositoryPage from "./pages/RepositoryPage";
import ReportPage from "./pages/ReportPage";
import RulesPage from "./pages/RulesPage";
import ScanPage from "./pages/ScanPage";
import UsersPage from "./pages/UsersPage";

/**
 * Route table (React Router v6 layout-route pattern).
 *
 * Shell is a <Route> WITHOUT a path: it wraps every non-login page as a
 * layout and renders the child page through <Outlet />. This is the canonical
 * v6 way to nest pages — a nested <Routes> inside a route element does not
 * resolve relative child paths reliably and leaves non-matching pages blank.
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<Shell />}>
            <Route index element={<DashboardPage />} />
            <Route path="scan" element={<ScanPage />} />
            <Route path="repository" element={<RepositoryPage />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="rules" element={<RulesPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="inspections/:token" element={<ReportPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}