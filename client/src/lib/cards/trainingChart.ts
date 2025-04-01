import * as d3 from 'd3';

interface ChartData {
    precision: number[];
    recall: number[];
    f1_score: number[];
    accuracy: number[];
}

interface LegendItem {
    label: string;
    color: string;
}

interface BarData {
    key: string;
    value: number;
}

export function createChart(chartData: ChartData, steps_training: string[]): void {
    // Clear previous chart
    d3.select("#chart").selectAll("*").remove();

    // Set up dimensions
    const margin = { top: 20, right: 100, bottom: 40, left: 100 };
    const width = 600;
    const height = 400;

    // Create SVG
    const svg = d3.select("#chart")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;");

    // Create scales
    const x0 = d3
        .scaleBand()
        .domain(steps_training)
        .rangeRound([margin.left, width - margin.right])
        .padding(0.1);

    const x1 = d3
        .scaleBand()
        .domain(["precision", "recall", "f1_score", "accuracy"])
        .rangeRound([0, x0.bandwidth()])
        .padding(0.05);

    const y = d3
        .scaleLinear()
        .domain([0, 1])
        .nice()
        .range([height - margin.bottom, margin.top]);

    const color = d3
        .scaleOrdinal()
        .domain(["precision", "recall", "f1_score", "accuracy"])
        .range(["#66c2a5", "#fc8d62", "#8da0cb", "#b3b3b3"]);

    // Create groups for each step
    const g = svg
        .append("g")
        .selectAll("g")
        .data(steps_training)
        .enter()
        .append("g")
        .attr("transform", (d: string) => `translate(${x0(d)},0)`);

    // Add X-axis
    svg
        .append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x0))
        .selectAll("text")
        .style("font-size", "12px")
        .style("text-anchor", "middle");

    // Add Y-axis
    svg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y))
        .style("font-size", "12px");

    // Draw bars
    g.selectAll("rect")
        .data((d: string) =>
            ["precision", "recall", "f1_score", "accuracy"].map((key: string) => ({
                key,
                value: chartData[key][steps_training.indexOf(d)],
            }))
        )
        .enter()
        .append("rect")
        .attr("x", (d: BarData) => x1(d.key))
        .attr("y", (d: BarData) => y(d.value))
        .attr("width", x1.bandwidth())
        .attr("height", (d: BarData) => y(0) - y(d.value))
        .attr("fill", (d: BarData) => color(d.key));

    // Add legend
    const legendData: LegendItem[] = [
        { label: "Precision", color: "#66c2a5" },
        { label: "Recall", color: "#fc8d62" },
        { label: "F1 Score", color: "#8da0cb" },
        { label: "Accuracy", color: "#b3b3b3" },
    ];

    const legend = svg
        .append("g")
        .attr("transform", `translate(${width - margin.right - 5}, 20)`);

    const legendItems = legend
        .selectAll(".legend")
        .data(legendData)
        .enter()
        .append("g")
        .attr("class", "legend")
        .attr("transform", (d: LegendItem, i: number) => `translate(0, ${i * 20})`);

    legendItems
        .append("rect")
        .attr("width", 18)
        .attr("height", 18)
        .attr("fill", (d: LegendItem) => d.color);

    legendItems
        .append("text")
        .attr("x", 24)
        .attr("y", 9)
        .attr("dy", ".35em")
        .style("font-size", "12px")
        .style("fill", "black")
        .text((d: LegendItem) => d.label);
}
