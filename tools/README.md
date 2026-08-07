# Outils de mesure

Scripts d'analyse, hors du plugin : ils ne sont ni installés ni
appelés par Stash. Ils servent à vérifier ce que le moteur vaut plutôt
qu'à le faire tourner.

| Script | Usage |
|---|---|
| `collecte_echantillon.py` | rejoue la collecte sur N fiches et conserve le détail par source (le plugin ne garde que la valeur retenue) |
| `valider_scoring.py` | méthode de la source retirée, avec témoins naïfs |
| `mesurer_fiabilites.py` | fiabilité réelle de chaque source, par champ |
| `essai_ponderations.py` | compare plusieurs formules de notation |

La collecte s'exécute dans le conteneur, les analyses sur l'hôte :

```bash
docker cp tools/collecte_echantillon.py <conteneur>:/root/.stash/plugins/gaizer/
docker exec <conteneur> python3 /root/.stash/plugins/gaizer/collecte_echantillon.py 70
docker cp <conteneur>:/tmp/echantillon_sources.json /tmp/
python3 tools/valider_scoring.py
python3 tools/mesurer_fiabilites.py
```

Comptez environ deux minutes par fiche : les scrapers sont lents et
l'écriture est incrémentale, l'analyse peut donc démarrer avant la fin.
