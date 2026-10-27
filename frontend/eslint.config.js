import pluginVue from 'eslint-plugin-vue'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  { name: 'app/arquivos', files: ['**/*.{ts,mts,tsx,vue}'] },
  { name: 'app/ignorados', ignores: ['**/dist/**', '**/dev-dist/**', 'src/api/schema.d.ts'] },
  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,
  skipFormatting,
)
