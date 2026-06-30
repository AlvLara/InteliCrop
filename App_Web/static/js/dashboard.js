document.addEventListener("DOMContentLoaded", () => {
    const btnVerPlantas = document.querySelector(".btn-ver-plantas");

    if (btnVerPlantas) {
        btnVerPlantas.addEventListener("click", () => {
            const url = btnVerPlantas.dataset.url;

            if (url) {
                window.location.href = url;
            }
        });
    }
});