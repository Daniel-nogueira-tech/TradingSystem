// candleWorker.js
self.onmessage = function(e) {
  const { data, lastTimestamp, startIndex } = e.data;
  
  // Filtra dados novos
  const startIdx = lastTimestamp 
    ? data.findIndex(c => c.tempo > lastTimestamp)
    : 0;
  
  if (startIdx === -1) {
    self.postMessage({ type: 'noNewData' });
    return;
  }
  
  // Pré-processa dados
  const processed = [];
  for (let i = startIdx; i < data.length; i++) {
    processed.push({
      ...data[i],
      close: Number(data[i].close),
      timestamp: new Date(data[i].tempo.replace(' ', 'T')).getTime()
    });
  }
  
  self.postMessage({ 
    type: 'newData', 
    data: processed,
    lastTimestamp: data[data.length - 1].tempo 
  });
};
