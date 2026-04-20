/**
 * CDK for Terraform: generates Terraform JSON under cdktf.out/.
 * Same GCP resources idea as infra/terraform — do not double-apply on the same project names.
 *
 * export GOOGLE_PROJECT=my-project
 * npm install && cdktf get && cdktf synth
 */
import { Construct } from "constructs";
import { App, TerraformStack, TerraformOutput } from "cdktf";
import { GoogleProvider } from "@cdktf/provider-google/lib/provider";
import { StorageBucket } from "@cdktf/provider-google/lib/storage-bucket";
import { ArtifactRegistryRepository } from "@cdktf/provider-google/lib/artifact-registry-repository";

class CreditScoringStack extends TerraformStack {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    const project =
      process.env.GOOGLE_PROJECT || process.env.GCLOUD_PROJECT || "REPLACE_ME";
    const region = "europe-central2";

    new GoogleProvider(this, "google", {
      project,
      region,
    });

    const bucket = new StorageBucket(this, "vector_embeddings", {
      name: `${project}-cdktf-emb-sample`,
      location: region,
      uniformBucketLevelAccess: true,
    });

    const repo = new ArtifactRegistryRepository(this, "app", {
      repositoryId: "millennium-credit-gke-docker",
      location: region,
      format: "DOCKER",
      description: "CDKTF sample — align name with your org",
    });

    new TerraformOutput(this, "bucket_name", {
      value: bucket.name,
    });
    new TerraformOutput(this, "artifact_registry_id", {
      value: repo.repositoryId,
    });
  }
}

const app = new App();
new CreditScoringStack(app, "credit-scoring-infra");
app.synth();
