import React from 'react'
import './Login.css'
import { Link } from 'react-router-dom'
const Login = () => {
    return (
        <div className='login-container'>
            <img src="./favicon.ico" alt="icon" className='icon-login' />

            <div className='dot' style={{ '--x': 1, '--y': 1 }}></div>
            <div className='dot' style={{ '--x': -1, '--y': 1 }}></div>
            <div className='dot' style={{ '--x': 1, '--y': -1 }}></div>
            <div className='dot' style={{ '--x': -1, '--y': -1 }}></div>

            <section className='login'>
                <div>
                    <h2>Login</h2>
                    <div className='input-login'>
                        <input type="text" placeholder='Digite seu email'/>

                    </div>
                    <div className='input-login'>
                        <input type="password"  placeholder='Digite sua senha'/>
                    </div>
                </div>
                <div>
                    <button className='longin-submit'>Entrar</button>
                    <Link to='/register' > <p className='login-register' style={{fontSize:'18px'}} >Criar conta</p></Link>
                </div>
            </section>
        </div>
    )
}

export default Login
