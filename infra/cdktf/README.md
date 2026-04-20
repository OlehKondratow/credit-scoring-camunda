# CDK for Terraform (TypeScript)

Генерирует **тот же Terraform**, что и классический HCL, но из TypeScript. Рабочий каталог: `cdktf.out/` после `cdktf synth`.

## Запуск

```bash
cd infra/cdktf
export GOOGLE_PROJECT=your-project-id
npm install
cdktf get
cdktf synth
# plan/apply через terraform в cdktf.out/stacks/... или cdktf deploy
```

Исправьте `REPLACE_ME` в `main.ts` или задайте `GOOGLE_PROJECT`. Не дублируйте имена бакетов/реп с уже созданными Terraform/Pulumi.
