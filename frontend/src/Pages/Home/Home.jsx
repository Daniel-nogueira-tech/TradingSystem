import React, { useState } from 'react';
import './Home.css';
import MyChart from '../../Components/MyChart/MyChart';
import Swal from 'sweetalert2';

const Home = () => {
    const [selectedDateStart, setSelectedDateStart] = useState('data');
    const [selectedDateEnd, setSelectedDateEnd] = useState('data');

    const onChangeHandlerDate = async () => {
        const { value: date } = await Swal.fire({
            title: "Selecione a data",
            input: "date",
            inputLabel: "Escolha uma data",
            inputPlaceholder: "Data",
            inputAttributes: {
                required: true,
            },
            customClass: {
                popup: 'fundo-preto',
                title: 'titulo-branco',
                inputLabel: 'label-branca',
                confirmButton: 'botao-verde',
                validationMessage: 'erro-custom'
            },
            didOpen: () => {
                const today = new Date().toISOString().split("T")[0];
                Swal.getInput().max = today;
            },
            preConfirm: (date) => {
                if (!date) {
                    Swal.showValidationMessage("Você precisa escolher uma data!");
                }
            }
        });
        if (date) {
            setSelectedDateStart(date);

            Swal.fire({
                title: 'Data selecionada:',
                text: date,
                customClass: {
                    popup: 'fundo-preto',
                    title: 'titulo-branco',
                    content: 'texto-branco',
                    confirmButton: 'botao-verde',
                }
            });

            // Aqui você pode disparar um fetch ou filtro com a data selecionada
            // Exemplo: fetchDataByDate(date);

        }
    };

    const onChangeHandlerDateEnd = async () => {
        const { value: date } = await Swal.fire({
            title: "Selecione a data",
            input: "date",
            inputLabel: "Escolha uma data",
            inputPlaceholder: "Data",
            inputAttributes: {
                required: true,
            },
            customClass: {
                popup: 'fundo-preto',
                title: 'titulo-branco',
                inputLabel: 'label-branca',
                confirmButton: 'botao-verde',
                validationMessage: 'erro-custom'
            },
            didOpen: () => {
                const today = new Date().toISOString().split("T")[0];
                Swal.getInput().max = today;
            },
            preConfirm: (date) => {
                if (!date) {
                    Swal.showValidationMessage("Você precisa escolher uma data!");
                }
            }
        });
        if (date) {
            setSelectedDateEnd(date);

            Swal.fire({
                title: 'Data selecionada:',
                text: date,
                customClass: {
                    popup: 'fundo-preto',
                    title: 'titulo-branco',
                    content: 'texto-branco',
                    confirmButton: 'botao-verde',
                }
            });


            // Aqui você pode disparar um fetch ou filtro com a data selecionada
            // Exemplo: fetchDataByDate(date);
        }
    };

    return (
        <div className='container-home-main '>
            <div className='container-home '>
                <div className='button-date-container'>
                    <div className='button-dt'>
                        <button className='button-date' onClick={onChangeHandlerDate}>Data inicio</button>
                        {selectedDateStart && <p className='date'>De: <strong>{selectedDateStart}</strong></p>}
                    </div>

                    <div className='button-dt'>
                        <button className='button-date' onClick={onChangeHandlerDateEnd}>Data final</button>
                        {selectedDateStart && <p className='date'>Até a : <strong>{selectedDateEnd}</strong></p>}
                    </div>
                    <button className='button-search' id='button-search'>
                        <img src="./search.svg" alt="" />
                    </button>
                </div>


                <div className='content-wrapper'>
                    <div className='container-home'>
                        <div className='container-results'>
                            <h3>Saldo atual</h3>
                            <p>R$ 25.354,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Lucro</h3>
                            <p>R$ 27.454,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Perdas</h3>
                            <p>R$ -20.654,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Retorno</h3>
                            <p>80%</p>
                        </div>
                        <div className='container-results'>
                            <h3>Vendido</h3>
                            <p>80</p>
                        </div>
                        <div className='container-results'>
                            <h3>Comprado</h3>
                            <p>10</p>
                        </div>
                        <div className='container-results'>
                            <h3>Total de operações</h3>
                            <p>125</p>
                        </div>
                        <div className='container-results'>
                            <h3>Taxa de acerto</h3>
                            <p>62%</p>
                        </div>
                        <div className='container-results'>
                            <h3>Maior lucro / maior perda</h3>
                            <p>Lucro: R$ 3.200,00</p>
                            <p>Perda: R$ -1.100,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Risco/Retorno</h3>
                            <p>1:2</p>
                        </div>
                        <div className='container-results'>
                            <h3>Tempo médio de operação</h3>
                            <p>2h 45min</p>
                        </div>
                        <div className='container-results'>
                            <h3>Drawdown</h3>
                            <p>-12%</p>
                        </div>
                        <div className='container-results'>
                            <h3>Média de ganhos</h3>
                            <p>R$ 2.542,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Média de perdas</h3>
                            <p>R$ -542,00</p>
                        </div>
                        <div className='container-results'>
                            <h3>Historico completo</h3>
                            <p></p>
                        </div>
                    </div>

                    <div className='analysis-chart'>
                        <MyChart selectedDateStart={selectedDateStart} selectedDateEnd={selectedDateEnd} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
