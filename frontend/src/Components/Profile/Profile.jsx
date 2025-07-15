import React from 'react';
import './Profile.css';

const Profile = () => {
  const user = {
    name: 'Lucas Silva',
    email: 'lucas@email.com',
    country: 'Brasil',
    role: 'Usuário',
    joined: '15 de março de 2024',
    balance:'15000',
    simulatedBalance:'12.200'
  };

  return (
    <div className='profile-main'>
      <div className='profile-card'>
        <h2>Perfil do Usuário</h2>
        <div className='profile-info'>
          <p><strong>Nome:</strong> {user.name}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>País:</strong> {user.country}</p>
          <p><strong>Nível de Acesso:</strong> {user.role}</p>
          <p><strong>Data de Cadastro:</strong> {user.joined}</p>
          <p><strong>Saldo Simulação:</strong> {user.simulatedBalance}</p>
          <p><strong>Saldo Real:</strong> {user.balance}</p>
        </div>
        <div className='button-profile'>
          <button className='save-button'>Atualizar</button>
          <button
            className='save-button'
            id='save-button'
          >Sair</button>
        </div>
      </div>

    </div>
  );
};

export default Profile;
