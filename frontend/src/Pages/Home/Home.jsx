import React, { useState } from 'react';
import './Home.css';           // ← o css atualizado acima
import MyChart from '../../Components/MyChart/MyChart';
import Swal from 'sweetalert2';


const Home = () => {
    const [selectedDateStart, setSelectedDateStart] = useState('');
    const [selectedDateEnd, setSelectedDateEnd] = useState('');

    const pickStartDate = async () => {
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

    const pickEndDate = async () => {
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

    const handleSearch = () => {
        // Aqui você pode chamar a busca / atualizar o gráfico
        console.log("Buscando:", selectedDateStart, "→", selectedDateEnd);
    };

    return (
        <div className="dashboard-wrapper">
            {/* Barra de filtros */}
            <div className="filters-bar">
                <div className="filter-group">
                    <button onClick={pickStartDate}>
                        {/* <Calendar size={18} />  ← opcional com lucide */}
                        Data Inicial
                    </button>
                    {selectedDateStart && (
                        <span className="date-display">De: <strong>{selectedDateStart}</strong></span>
                    )}
                </div>

                <div className="filter-group">
                    <button onClick={pickEndDate}>Data Final</button>
                    {selectedDateEnd && (
                        <span className="date-display">Até: <strong>{selectedDateEnd}</strong></span>
                    )}
                </div>

                <button className="btn-search" onClick={handleSearch}>
                    <span className='pi pi-search'></span>
                </button>
            </div>

            {/* KPIs em grid */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <h3>Saldo Atual</h3>
                    <p className="kpi-neutral">R$ 25.354,00</p>
                </div>
                <div className="kpi-card">
                    <h3>Lucro</h3>
                    <p className="kpi-positive">R$ 27.454,00</p>
                </div>
                <div className="kpi-card">
                    <h3>Perdas</h3>
                    <p className="kpi-negative">R$ -2.654,00</p>
                </div>
                <div className="kpi-card">
                    <h3>Retorno</h3>
                    <p className="kpi-positive">80%</p>
                </div>
                <div className="kpi-card">
                    <h3>Taxa de Acerto</h3>
                    <p className="kpi-positive">62%</p>
                </div>
                <div className="kpi-card">
                    <h3>Drawdown</h3>
                    <p className="kpi-negative">-12%</p>
                </div>
            
                <div className="kpi-card">
                    <h3>Histórico</h3>
                    <p className="kpi-grid pi pi-history"></p>
                </div>

                {/* Adicione mais conforme necessário – priorize os 5–7 mais importantes aqui */}
            </div>

            {/* Gráfico principal – ocupa mais espaço */}
            <div className="chart-section">
                <h2>Análise de Performance</h2>
                <MyChart selectedDateStart={selectedDateStart} selectedDateEnd={selectedDateEnd} />
            </div>

            {/* Você pode adicionar mais seções abaixo: tabela de operações, histórico etc */}
        </div>
    );
};

export default Home;