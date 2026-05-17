const riskForm = document.getElementById("riskForm");
const uploadBtn = document.getElementById("uploadBtn");
const statusMessage = document.getElementById("statusMessage");
const riskLabel = document.getElementById("riskLabel");
const riskMessage = document.getElementById("riskMessage");

const stockForm = document.getElementById("stockSearchForm");
const newsForm = document.getElementById("newsSearchForm");

function csrfToken() {
    return document.querySelector("meta[name='csrf-token']").content;
}

function showStatus(element, message, type) {
    element.textContent = message;
    element.dataset.type = type || "info";
}

function updateRiskCircle(score) {
    const circle = document.querySelector(".circle");
    const riskValue = document.getElementById("riskValue");
    const finalScore = Number(score) || 0;

    let color = "#22c55e";

    if (finalScore >= 70) {
        color = "#ef4444";
    } else if (finalScore >= 40) {
        color = "#f59e0b";
    }

    riskValue.textContent = finalScore + "%";
    riskValue.style.color = color;
    circle.style.background = `conic-gradient(${color} ${finalScore * 3.6}deg, rgba(255,255,255,0.18) 0deg)`;
}

function showRiskResult(data, source) {
    updateRiskCircle(data.score);
    riskLabel.textContent = data.prediction;
    riskMessage.textContent = `${source} analysis completed with ${data.score}% confidence.`;
    showStatus(statusMessage, "Analysis complete", "success");
}

riskForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const text = document.getElementById("financialText").value.trim();

    if (text === "") {
        showStatus(statusMessage, "Please enter some text.", "error");
        return;
    }

    showStatus(statusMessage, "Analyzing text...", "info");

    try {
        const response = await fetch("/api/predict/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken()
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (!response.ok) {
            showStatus(statusMessage, data.error || "Analysis failed.", "error");
            return;
        }

        showRiskResult(data, "Text");
    } catch (error) {
        showStatus(statusMessage, "Something went wrong.", "error");
    }
});

uploadBtn.addEventListener("click", async function () {
    const file = document.getElementById("pdfFile").files[0];

    if (!file) {
        showStatus(statusMessage, "Please choose a PDF file.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("pdf", file);

    showStatus(statusMessage, "Uploading PDF...", "info");

    try {
        const response = await fetch("/api/upload-pdf/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken()
            },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showStatus(statusMessage, data.error || "PDF analysis failed.", "error");
            return;
        }

        showRiskResult(data, "PDF");
    } catch (error) {
        showStatus(statusMessage, "PDF upload failed.", "error");
    }
});

document.querySelectorAll(".tab-button").forEach(function (button) {
    button.addEventListener("click", function () {
        document.querySelectorAll(".tab-button").forEach(function (item) {
            item.classList.remove("active");
        });

        document.querySelectorAll(".tab-panel").forEach(function (panel) {
            panel.classList.remove("active");
        });

        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
    });
});

async function getJson(url) {
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Could not load data.");
    }

    return data;
}

function drawChart(points) {
    const canvas = document.getElementById("stockChart");
    const ctx = canvas.getContext("2d");
    const prices = points.map(function (point) {
        return point.price;
    });

    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    const padding = 30;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#5eead4";
    ctx.lineWidth = 3;
    ctx.beginPath();

    points.forEach(function (point, index) {
        const x = padding + (index / (points.length - 1)) * (canvas.width - padding * 2);
        const y = canvas.height - padding - ((point.price - min) / range) * (canvas.height - padding * 2);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();
}

function showStock(data) {
    const changeSign = data.change >= 0 ? "+" : "";
    const changeLabel = document.getElementById("stockChangeLabel");

    document.getElementById("stockSymbolLabel").textContent = data.symbol;
    document.getElementById("stockPriceLabel").textContent = "$" + data.price;

    changeLabel.textContent = `${changeSign}${data.change} (${changeSign}${data.change_percent}%)`;
    changeLabel.dataset.trend = data.change >= 0 ? "up" : "down";

    drawChart(data.points);
}

async function loadStock(symbol) {
    const marketStatus = document.getElementById("marketStatus");
    showStatus(marketStatus, "Loading stock data...", "info");

    try {
        const data = await getJson("/api/market/search/?symbol=" + encodeURIComponent(symbol));
        showStock(data);
        showStatus(marketStatus, "Stock data loaded", "success");
    } catch (error) {
        showStatus(marketStatus, error.message, "error");
    }
}

async function loadTopCompanies() {
    const box = document.getElementById("topCompanies");

    try {
        const data = await getJson("/api/market/top/");
        box.innerHTML = "";

        data.companies.forEach(function (company) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "company-card";
            button.innerHTML = `
                <span>
                    <strong>${company.symbol}</strong>
                    <small>${company.name}</small>
                </span>
                <em>${company.change_percent}%</em>
            `;
            button.addEventListener("click", function () {
                document.getElementById("stockSymbol").value = company.symbol;
                loadStock(company.symbol);
            });
            box.appendChild(button);
        });
    } catch (error) {
        box.innerHTML = `<p class="muted-text">${error.message}</p>`;
    }
}

async function loadNews(query) {
    const newsStatus = document.getElementById("newsStatus");
    const newsList = document.getElementById("newsList");

    showStatus(newsStatus, "Loading news...", "info");

    try {
        const data = await getJson("/api/news/?q=" + encodeURIComponent(query));
        newsList.innerHTML = "";

        data.articles.forEach(function (article) {
            newsList.innerHTML += `
                <article class="panel news-card">
                    <span>${article.source}</span>
                    <h3>${article.title}</h3>
                    <p>${article.published}</p>
                    <a href="${article.link}" target="_blank" rel="noopener noreferrer">Read more</a>
                </article>
            `;
        });

        showStatus(newsStatus, "News loaded", "success");
    } catch (error) {
        newsList.innerHTML = `<article class="panel"><p class="muted-text">${error.message}</p></article>`;
        showStatus(newsStatus, error.message, "error");
    }
}

stockForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const symbol = document.getElementById("stockSymbol").value.trim();

    if (symbol !== "") {
        loadStock(symbol);
    }
});

newsForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const query = document.getElementById("newsQuery").value.trim() || "financial markets";
    loadNews(query);
});

loadStock("NVDA");
loadTopCompanies();
loadNews("financial markets");
