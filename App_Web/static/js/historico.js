document.addEventListener("DOMContentLoaded", function () {
    const btnCambiar = document.getElementById("btn-cambiar-vista");
    const vistaTabla = document.getElementById("vista-tabla");
    const vistaGrafica = document.getElementById("vista-grafica");
    let graficoInstance = null;

    if (!btnCambiar) return;

    // Alternar visibilidad al hacer click
    btnCambiar.addEventListener("click", function () {
        if (vistaTabla.style.display !== "none") {
            vistaTabla.style.display = "none";
            vistaGrafica.style.display = "block";
            btnCambiar.innerHTML = "Ver como Tabla";
            
            if (!graficoInstance) {
                cargarGrafica();
            }
        } else {
            vistaTabla.style.display = "block";
            vistaGrafica.style.display = "none";
            btnCambiar.innerHTML = "Ver como Gráfica";
        }
    });

    function cargarGrafica() {
        const uuidCultivo = window.location.pathname.split("/").pop();

        fetch(`/cultivo_historico_data/${uuidCultivo}`)
            .then(response => response.json())
            .then(res => {
                if (!res.ok) {
                    alert("Error al obtener los datos del gráfico.");
                    return;
                }

                const historial = res.historial.reverse();

                const labels = historial.map(r => {
                    const f = new Date(r.created_at);
                    return f.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' }) + 
                           ' ' + 
                           f.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
                });
                
                const temp = historial.map(r => r.data.temperatura);
                const humAire = historial.map(r => r.data.humedad);
                const humSuelo = historial.map(r => r.data.humedad_suelo);

                const ctx = document.getElementById('graficoHistorico').getContext('2d');
                
                graficoInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Temp. (°C)',
                                data: temp,
                                borderColor: '#ef4444',
                                backgroundColor: 'transparent',
                                borderWidth: 2,
                                tension: 0.2
                            },
                            {
                                label: 'Hum. Aire (%)',
                                data: humAire,
                                borderColor: '#3b82f6',
                                backgroundColor: 'transparent',
                                borderWidth: 2,
                                tension: 0.2
                            },
                            {
                                label: 'Hum. Suelo (%)',
                                data: humSuelo,
                                borderColor: '#10b981',
                                backgroundColor: 'transparent',
                                borderWidth: 2,
                                tension: 0.2
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top' }
                        },
                        scales: {
                            x: { grid: { display: false } },
                            y: { beginAtZero: false }
                        }
                    }
                });
            })
            .catch(err => console.error("Error cargando gráfica:", err));
    }
});