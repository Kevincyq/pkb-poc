import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import Home from './pages/Home/index';  // 导入功能完整的Home组件
import CollectionDetail from './pages/Collection/Detail';

//路由配置
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: '/collection/:categoryName',
        element: <CollectionDetail />,
      },
    ],
  },
]);

export default router;