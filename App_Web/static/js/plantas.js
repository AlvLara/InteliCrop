document.addEventListener("DOMContentLoaded", () => {
    const botonesRegistroPlanta = document.querySelectorAll(".js-ir-registro-planta");
    const botonesVerCultivo = document.querySelectorAll(".js-ver-cultivo");
    const formulariosEliminar = document.querySelectorAll(".delete-plant-form");

    botonesRegistroPlanta.forEach((boton) => {
        boton.addEventListener("click", () => {
            const url = boton.dataset.url;

            if (url) {
                window.location.href = url;
            }
        });
    });

    botonesVerCultivo.forEach((boton) => {
        boton.addEventListener("click", () => {
            const url = boton.dataset.url;

            if (url) {
                window.location.href = url;
            }
        });
    });

    formulariosEliminar.forEach((formulario) => {
        formulario.addEventListener("submit", (event) => {
            nombrePlanta = formulario.dataset.nombre_planta
            const confirmado = window.confirm("¿Seguro que quieres eliminar la planta " + nombrePlanta + "?");

            if (!confirmado) {
                event.preventDefault();
            }
        });
    });
});