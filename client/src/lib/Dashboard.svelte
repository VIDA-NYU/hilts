<script>
    // core components
    import LineChart from "./cards/LineChart.svelte";
    import BarChart from "./cards/BarChart.svelte";
    // import CardPageVisits from "cards/CardPageVisits.svelte";
    // import CardSocialTraffic from ".cards/CardSocialTraffic.svelte";
    export let location;
  </script>

  <div>
    <div class="flex flex-wrap">
      <div class="w-full xl:w-8/12 mb-12 xl:mb-0 px-4">
        <LineChart />
      </div>
      <div class="w-full xl:w-4/12 px-4">
        <BarChart />
      </div>
    </div>
    <div class="flex flex-wrap mt-4">
      <div class="w-full xl:w-8/12 mb-12 xl:mb-0 px-4">
        <LineChart />
      </div>
      <div class="w-full xl:w-4/12 px-4">
        <BarChart />
      </div>
    </div>
  </div>
