import React from 'react'
import './MyChart.css'
import ChartPerformance from './ChartPerformance'
import ChartPerforPie from './ChartPerforPie'

const MyChart = ({ selectedDateStart,selectedDateEnd }) => {
  return (
    <div className='MyChart'>
      <div className='MyChart-analysis'>
        <ChartPerformance selectedDateStart={selectedDateStart} selectedDateEnd={selectedDateEnd}/>
      </div>
      <div className='MyChart-analysis'>
        <ChartPerforPie selectedDateStart={selectedDateStart} />
      </div>
    </div>
  )
}

export default MyChart
