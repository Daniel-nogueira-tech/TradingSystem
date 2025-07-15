import React from 'react';
import './SideBar.css';
import { FaChartBar, FaHome, FaUserAlt, FaCog, FaChartLine } from 'react-icons/fa';
import { NavLink } from 'react-router-dom';

const SideBar = () => {
  return (
    <div className="container-side">
      <div className='menu'>

        <div className='logo-container'>
          <img src="./favicon.ico" alt="logo" className='logo' />
          <p>Next Atom</p>
        </div>
        
        <NavLink to="/" className="side-button">
          <FaHome className="icon" />
          <span>Início</span>
        </NavLink >


        <NavLink to="/Graphics" className="side-button">
          <FaChartBar className="icon" />
          <span>Gráficos</span>
        </NavLink >

        <NavLink to="/Market" className="side-button">
          <FaChartLine className="icon" />
          <span>Mercados</span>
        </NavLink >

        <NavLink to="/Correlation" className="side-button">
          <FaChartLine className="icon" />
          <span>Correlação</span>
        </NavLink >
      </div>

      <div className='config'>
        <NavLink to="/Profile" className="side-button">
          <FaUserAlt className="icon" />
          <span>Perfil</span>
        </NavLink >

        <NavLink to="/Config" className="side-button">
          <FaCog className="icon" />
          <span>Config</span>
        </NavLink>
      </div>
    </div>
  );
};

export default SideBar;
