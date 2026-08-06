document.addEventListener("DOMContentLoaded", function () {

    function readJsonValue(id) {

        const element = document.getElementById(id);

        if (!element) {
            return 0;
        }

        try {

            const value = JSON.parse(element.textContent);

            return Number(value || 0);

        } catch (error) {

            console.error("JSON parse error for:", id, error);

            return 0;
        }
    }

    const totalCurrent = readJsonValue("current-demand");
    const totalFuture = readJsonValue("future-demand");

    const demandCanvas =
        document.getElementById("demandChart");

    const pieCanvas =
        document.getElementById("pieChart");

    if (typeof Chart === "undefined") {

        console.error(
            "Chart.js is not loaded. Please check CDN script."
        );

        return;
    }

    if (demandCanvas) {

        new Chart(demandCanvas, {

            type: "bar",

            data: {

                labels: [
                    "Current Demand",
                    "Future Demand"
                ],

                datasets: [{
                    label: "Manpower Demand",

                    data: [
                        totalCurrent,
                        totalFuture
                    ],

                    backgroundColor: [
                        "#2563eb",
                        "#16a34a"
                    ],

                    borderRadius: 12,

                    barThickness: 70

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    "Demand: " +
                                    context.raw
                                );

                            }

                        }

                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
                        }

                    }

                }

            }

        });

    }

    if (pieCanvas) {

        new Chart(pieCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Current Demand",
                    "Future Demand"
                ],

                datasets: [{

                    data: [
                        totalCurrent,
                        totalFuture
                    ],

                    backgroundColor: [
                        "#2563eb",
                        "#16a34a"
                    ],

                    borderColor: "#ffffff",

                    borderWidth: 4

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                cutout: "60%",

                plugins: {

                    legend: {
                        position: "bottom"
                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    context.label +
                                    ": " +
                                    context.raw
                                );

                            }

                        }

                    }

                }

            }

        });

    }

});