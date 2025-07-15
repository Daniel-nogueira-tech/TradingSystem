import React from 'react'
import './Login.css'
import { Link } from 'react-router-dom'
const Register = () => {
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
                        <input type="text" placeholder='Seu nome' />

                    </div>
                    <div className='input-login' >
                        <input type="password" placeholder='Digite seu email' />
                    </div>
                    <div className='input-login'>
                        <input type="password" placeholder='Digite uma senha' />
                    </div>
                    <div className='input-login'>
                        <input type="password" placeholder='Confirme sua senha' />
                    </div>
                </div>
                <div>
                    <button className='longin-submit'>Registrar</button>
                    <Link to='/login' > <p className='login-register' style={{ fontSize: '18px' }} >Entrar</p></Link>
                </div>
            </section>
        </div>
    )
}

export default Register
