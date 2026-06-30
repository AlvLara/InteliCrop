const REFRESH_INTERVAL_MS = 10000;

function reiniciarAnimacionSensores() {
  const iconos = document.querySelectorAll(".sensor-icon");

  iconos.forEach((icono) => {
    icono.classList.remove("sensor-loading");

    // Fuerza el reinicio de la animación CSS
    void icono.offsetWidth;

    icono.classList.add("sensor-loading");
  });
}

function convertirABooleano(valor) {
  if (valor === true || valor === 1 || valor === "1") {
    return true;
  }

  if (valor === "true" || valor === "True" || valor === "sí" || valor === "Si" || valor === "SI") {
    return true;
  }

  return false;
}

function obtenerUmbrales() {
  const divCultivo = document.getElementById("cultivo-data");

  if (!divCultivo) {
    return {};
  }

  const rawUmbrales = divCultivo.getAttribute("data-umbrales");

  if (!rawUmbrales) {
    return {};
  }

  try {
    return JSON.parse(rawUmbrales);
  } catch (error) {
    console.error("Error al leer los umbrales:", error);
    return {};
  }
}

function actualizarGemeloDigital(lectura, umbrales) {
  const digitalTwin = document.getElementById("digital-twin");
  const estadoPlanta = document.getElementById("estado-planta");
  const badgeTemp = document.getElementById("badge-temp");
  const badgeSuelo = document.getElementById("badge-suelo");
  const badgeLluvia = document.getElementById("badge-lluvia");

  if (!digitalTwin) {
    return;
  }

  const temperatura = Number(lectura.temperatura);
  const humedadSuelo = Number(lectura.humedad_suelo);
  const estaLloviendo = convertirABooleano(lectura.esta_lloviendo);

  const tempMin = umbrales.temperatura?.min ?? 10;
  const tempMax = umbrales.temperatura?.max ?? 32;

  const sueloMin = umbrales.humedad_suelo?.min ?? 30;
  const sueloMax = umbrales.humedad_suelo?.max ?? 75;

  digitalTwin.classList.remove(
    "twin-hot",
    "twin-cold",
    "twin-ok",
    "twin-dry",
    "twin-wet",
    "twin-raining"
  );

  let estado = "Estado: cultivo estable";

  if (temperatura >= tempMax) {
    digitalTwin.classList.add("twin-hot");
  } else if (temperatura <= tempMin) {
    digitalTwin.classList.add("twin-cold");
  }

  if (humedadSuelo < sueloMin) {
    digitalTwin.classList.add("twin-dry");
    estado = "Estado: suelo seco, necesita riego";
  } else if (humedadSuelo > sueloMax) {
    digitalTwin.classList.add("twin-wet");
    estado = "Estado: suelo muy húmedo";
  } else {
    digitalTwin.classList.add("twin-ok");
    estado = "Estado: cultivo saludable";
  }

  if (estaLloviendo) {
    digitalTwin.classList.add("twin-raining");
  }

  if (estadoPlanta) {
    estadoPlanta.textContent = estado;
  }

  if (badgeTemp) {
    badgeTemp.textContent = `Temperatura: ${temperatura} °C`;
  }

  if (badgeSuelo) {
    badgeSuelo.textContent = `Suelo: ${humedadSuelo} %`;
  }

  if (badgeLluvia) {
    badgeLluvia.textContent = estaLloviendo ? "Lluvia: Sí" : "Lluvia: No";
  }
}

async function fetchData() {
  try {
    const divCultivo = document.getElementById("cultivo-data");

    if (!divCultivo) {
      return;
    }

    const uuidCultivo = divCultivo.getAttribute("data-uuid");
    const umbrales = obtenerUmbrales();

    const response = await fetch(`/cultivo_last_data/${uuidCultivo}`);

    if (!response.ok) {
      throw new Error(`Error en el servidor: ${response.status}`);
    }

    const data = await response.json();

    if (data.ok && data.last_data && data.last_data.data) {
      const lectura = data.last_data.data;

      const temperatura = document.getElementById("temperatura");
      const humedad = document.getElementById("humedad");
      const humedadSuelo = document.getElementById("humedad_suelo");
      const lluvia = document.getElementById("lluvia");
      const estaLloviendo = document.getElementById("esta_lloviendo");
      const elTimeEnvio = document.getElementById("ts");

      if (temperatura) {
        temperatura.textContent = `${lectura.temperatura} °C`;
      }

      if (humedad) {
        humedad.textContent = `${lectura.humedad} %`;
      }

      if (humedadSuelo) {
        humedadSuelo.textContent = `${lectura.humedad_suelo} %`;
      }

      if (lluvia) {
        lluvia.textContent = lectura.lluvia;
      }

      if (estaLloviendo) {
        estaLloviendo.textContent = convertirABooleano(lectura.esta_lloviendo) ? "Sí 🌧️" : "No ☀️";
      }

      actualizarGemeloDigital(lectura, umbrales);

      if (elTimeEnvio && data.last_data.created_at) {
        const fecha = new Date(data.last_data.created_at);
        elTimeEnvio.textContent = fecha.toLocaleString("es-ES");
      }
    } else {
      console.warn("Estructura de datos desconocida o vacía:", data.error);
    }

  } catch (error) {
    console.error("Error en la comunicación con la API:", error);
  } finally {
    reiniciarAnimacionSensores();
  }
}

function configurarBotonAlertas(uuidCultivo) {
  const btnAlertas = document.getElementById("btn-alertas");

  if (!btnAlertas) {
    return;
  }

  btnAlertas.addEventListener("click", () => {
    if (typeof visualizarAlertas === "function") {
      visualizarAlertas(uuidCultivo);
    } else {
      console.warn("La función visualizarAlertas no está definida.");
    }
  });
}

function configurarFormularioBomba() {
  const formBomba = document.getElementById("form-bomba");

  if (!formBomba) {
    return;
  }

  formBomba.addEventListener("submit", function (event) {
    const confirmar = confirm("¿Quieres activar la bomba de agua manualmente?");

    if (!confirmar) {
      event.preventDefault();
    }
  });
}

function configurarEdicionNombre() {
  const btnEditar = document.getElementById('btn-editar-nombre');
  const btnCancelar = document.getElementById('btn-cancelar-edicion');
  const formEditar = document.getElementById('form-editar-nombre');
  const displayNombre = document.getElementById('nombre-cultivo-display');

  if (btnEditar && btnCancelar && formEditar && displayNombre) {
    
    btnEditar.addEventListener('click', function () {
      formEditar.style.display = 'flex';
      btnEditar.style.display = 'none';
      displayNombre.style.display = 'none';
    });

    btnCancelar.addEventListener('click', function () {
      formEditar.style.display = 'none';
      btnEditar.style.display = 'block';
      displayNombre.style.display = 'block';
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const cultivoData = document.getElementById("cultivo-data");

  if (!cultivoData) {
    return;
  }

  const uuidCultivo = cultivoData.dataset.uuid;

  configurarBotonAlertas(uuidCultivo);
  configurarFormularioBomba();
  configurarEdicionNombre();

  fetchData();
  setInterval(fetchData, REFRESH_INTERVAL_MS);
});