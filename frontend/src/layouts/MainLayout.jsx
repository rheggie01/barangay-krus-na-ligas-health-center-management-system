import {
  Outlet,
} from "react-router-dom";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";


function MainLayout() {
  return (
    <div className="app-shell">

      <Sidebar />

      <div className="app-content">

        <Header />

        <main className="page-content">
          <Outlet />
        </main>

      </div>

    </div>
  );
}


export default MainLayout;