<script lang="ts">
  import type { Hit } from "./Api";
  import * as api from "./Api";

  export let hit: Hit;
  $: parsedHitMetadata = hit.metadata;
  $: hitLabels = hit.labels_types_dict;


  let result: Promise<Hits> | null = null;
  let limit: string = "16";
  let allSelectedData: {[key: string]: boolean; };
  let projectId: string = "default";

  export function getHits(imagePaths) {
      result = SellerSearch(queryStr, +limit, excludeLabeled);
      result.then( (hits: Hits) => {
        if (result) {
          const imagePaths = hits.hits.map((item) => ({[item.image_path]: true}));
          selectedDataStore.update((storeSelectedData) => {
            return { ...Object.assign({}, ...imagePaths) };
          });
        }
      });
    }



</script>
