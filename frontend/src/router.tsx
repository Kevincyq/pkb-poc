import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import Home from './pages/Home/index';  // 导入功能完整的Home组件
import CollectionDetail from './pages/Collection/Detail';
import LoginPage from './pages/Login/index';
import AuthCallback from './pages/AuthCallback/index';
import AuthGuard from './components/AuthGuard/index';

//路由配置
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: (
          <AuthGuard>
            <Home />
          </AuthGuard>
        ),
      },
      {
        path: '/collection/:categoryName',
        element: (
          <AuthGuard>
            <CollectionDetail />
          </AuthGuard>
        ),
      },
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/auth/callback',
        element: <AuthCallback />,
      },
      {
        path: '/api/auth/callback/:provider',
        element: <AuthCallback />,
      },
    ],
  },
]);

export default router;