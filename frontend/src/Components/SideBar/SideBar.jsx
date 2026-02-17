import React from 'react';
import './SideBar.css';
import { FaSignal , FaHome, FaUserAlt, FaCog, FaChartLine} from 'react-icons/fa';
import { BsRobot } from "react-icons/bs";
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
          <BsRobot className="icon" />
          <span>Algoritmo (IA)</span>
        </NavLink >

        <NavLink to="/Market" className="side-button">
          <FaChartLine className="icon" />
          <span>Mercados</span>
        </NavLink >

        <NavLink to="/Correlation" className="side-button">
          <FaSignal  className="icon" />
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
