import { Route, Routes, useLocation } from 'react-router-dom'
import './App.css'
import Home from './Pages/Home/Home';
import SideBar from './Components/SideBar/SideBar';
import Graphics from './Components/Graphics/Graphics';
import Profile from './Components/Profile/Profile';
import Config from './Components/Config/Config';
import Market from './Components/Market/Market';
import SiderBarRight from './Components/SiderBarRight/SiderBarRight';
import Correlation from './Components/Correlation/Correlation';
import Login from './Components/Login/Login';
import Register from './Components/Login/Register';


function App() {
const location = useLocation();
  return (
    <>
     {location.pathname !== '/login' && location.pathname !==  '/register' && <SideBar />}
      <div>
        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/Graphics' element={<Graphics />} />
          <Route path='/Profile' element={<Profile />} />
          <Route path='/Config' element={<Config />} />
          <Route path='/Market' element={<Market />} />
          <Route path='/Correlation' element={<Correlation/>} />
          <Route path='/login' element={<Login/>} />
          <Route path='/register' element={<Register/>} />
        </Routes>
      </div>
     {location.pathname === '/Graphics' &&  <SiderBarRight />}
    </>
  )
}

export default App
