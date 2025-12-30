// frontend/src/types/social.ts

import { components } from "@/lib/api-schema"; // O arquivo gerado automaticamente

// Extraímos os tipos diretamente do Schema do Backend
// Se o nome no serializer mudar, o TypeScript vai gritar aqui (Segurança Total)

export type FamilyRecipe = components["schemas"]["FamilyRecipeRead"];
export type FamilyRecipeInput = components["schemas"]["FamilyRecipeWrite"];
export type Allergen = components["schemas"]["Allergen"];
export type AllergenSeverity = components["schemas"]["AllergenSeverityEnum"]; // Enum gerado

// Tipos auxiliares que talvez não tenham schemas explícitos mas são usados
export type RecipeStatus = FamilyRecipe["status"];