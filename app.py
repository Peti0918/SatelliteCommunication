import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
import networkx as nx
import cartopy.crs as ccrs
from visualizer import Visualizer2D


class App:
    def __init__(self, satellites, times, ground_stations, dynamic_graphs, threshold, running, key_model, link_model,):

        self.satellites = satellites
        self.times = times
        self.ground_stations = ground_stations
        self.dynamic_graphs = dynamic_graphs
        self.threshold = threshold
        self.running = running
        self.current_frame = 0

        self.key_model = key_model
        self.link_model = link_model

        self.viz = Visualizer2D(satellites, times, ground_stations, threshold)

        # Közös matplotlib ablak
        self.fig = plt.figure(figsize=(10, 6))

        # Ebben tároljuk a különböző nézeteket (menü, térkép, hálózat, eleváció).
        # Minden nézethez eltesszük a hozzá tartozó tengelyt és widgeteket.
        self.views = {}

        self._create_menu_view()
        self._create_elevation_view()
        self._create_map_view()
        self._create_network_view()
        self._create_keyrate_view() 
        self._create_network_eskr_view()
        self._create_pair_flow_view()

        candidates = self._find_multisat_pair_flows(min_satellites=2)

        print("\n=== LEGJOBB LEGALÁBB 2 MŰHOLDAS PAIR FLOW PÁROK ===") #átmeneti

        for c in candidates[:10]:
            print(
                f"{c['src']} -> {c['dst']} | "
                f"active_steps={c['active_steps']} | "
                f"generated_bits={c['generated_bits']:.2e} bit | "
                f"best_rate={c['best_rate']:.2f} bit/s | "
                f"best_frame={c['best_frame']} | "
                f"satellites_in_path={c['satellite_count']}"
            )
            print("  path:", " -> ".join(c["best_path"])) #átmeneti

        # Induláskor a menü látszódjon.
        self.switch_view("menu")

    def _frame_iter(self, start=0):
        # Végtelen frame-generátor.
        # Az animáció ezt használja, így a frame-ek körbeérnek,
        # azaz az utolsó után újra 0 következik.
        n = len(self.times)
        i = start
        while True:
            yield i
            i = (i + 1) % n

    def _short_sat_label(self, full_name):
        # Rövidebb, olvashatóbb műholdfelirat készítése.
        # Erre azért van szükség, mert a teljes nevek gyakran túl hosszúak.
        if not isinstance(full_name, str):
            return str(full_name)

        # Ha van kötőjel a névben, akkor a jobb oldali rész végét megtartjuk,
        # mert az szokta a műholdak egyediségét mutatni.
        if '-' in full_name:
            left, right = full_name.rsplit('-', 1)
            if right:
                return f"{left}-{right[-3:]}"

        # Ha nincs jobb megoldás, az első 10 karaktert mutatjuk.
        return full_name[:10]

    def switch_view(self, name):

        # Nézetváltáskor először felszabadítjuk a widget lockot, ha épp foglalt.
        if self.fig.canvas.widgetlock.locked():
            self.fig.canvas.widgetlock.release(self.fig.canvas.widgetlock._owner)

        
        if hasattr(self, 'anim_map'):
            self.anim_map.event_source.stop()
        if hasattr(self, 'anim_net'):
            self.anim_net.event_source.stop()

        
        for v in self.views.values():
            v["axes"].set_visible(False)
            for extra_ax in v.get("extra_axes", []):
                extra_ax.set_visible(False)
            for w in v["widgets"]:
                w.ax.set_visible(False)
                w.set_active(False)

        
        view = self.views[name]
        view["axes"].set_visible(True)

        for extra_ax in view.get("extra_axes", []):
            extra_ax.set_visible(True)
            
        for w in view["widgets"]:
            w.ax.set_visible(True)
            w.set_active(True)


        if name == "map" and hasattr(self, '_update_map'):
            self._update_map(self.current_frame)
            if self.running and hasattr(self, 'anim_map'):
                
                self.anim_map.frame_seq = self._frame_iter((self.current_frame + 1) % len(self.times))
                self.anim_map.event_source.start()

        elif name == "network" and hasattr(self, '_update_net'):
            self._update_net(self.current_frame)
            if self.running and hasattr(self, 'anim_net'):
                self.anim_net.frame_seq = self._frame_iter((self.current_frame + 1) % len(self.times))
                self.anim_net.event_source.start()

        
        self.fig.canvas.draw_idle()

    def _deferred_switch(self, name):

        
        timer = self.fig.canvas.new_timer(interval=100)
        timer.single_shot = True
        timer.add_callback(lambda: self.switch_view(name))
        timer.start()

    def _create_menu_view(self):
        ax = self.fig.add_subplot(111)
        ax.set_axis_off()
        ax.text(0.5, 0.87, "Satellite Com Simulator", ha='center', fontsize=16, weight='bold')

        btn_map_ax = self.fig.add_axes([0.35, 0.68, 0.3, 0.07])
        btn_net_ax = self.fig.add_axes([0.35, 0.58, 0.3, 0.07])
        btn_elev_ax = self.fig.add_axes([0.35, 0.48, 0.3, 0.07])
        btn_key_ax = self.fig.add_axes([0.35, 0.38, 0.3, 0.07])
        btn_net_eskr_ax = self.fig.add_axes([0.35, 0.28, 0.3, 0.07])
        btn_pair_flow_ax = self.fig.add_axes([0.35, 0.18, 0.3, 0.07])

        btn_map = Button(btn_map_ax, "Open 2D Map")
        btn_net = Button(btn_net_ax, "View Network Graph")
        btn_elev = Button(btn_elev_ax, "View Elevation Graph")
        btn_key = Button(btn_key_ax, "View Key Rate Analysis")
        btn_net_eskr = Button(btn_net_eskr_ax, "View Network ESKR")
        btn_pair_flow = Button(btn_pair_flow_ax, "View Pair Flow")

        btn_map.on_clicked(lambda e: self._deferred_switch("map"))
        btn_net.on_clicked(lambda e: self._deferred_switch("network"))
        btn_elev.on_clicked(lambda e: self._deferred_switch("elevation"))
        btn_key.on_clicked(lambda e: self._deferred_switch("keyrate"))
        btn_net_eskr.on_clicked(lambda e: self._deferred_switch("network_eskr"))
        btn_pair_flow.on_clicked(lambda e: self._deferred_switch("pair_flow"))

        self.views["menu"] = {
            "axes": ax,
            "widgets": [btn_map, btn_net, btn_elev, btn_key, btn_net_eskr, btn_pair_flow]
        }

    def _create_network_view(self):
        # Hálózati topológia nézet.
        ax = self.fig.add_subplot(111)
        ax.set_axis_off()
        ax.set_title("Temporal Network Topology", pad=20, fontsize=14, weight='bold')

        # Ebbe a szótárba kerül minden csomópont 2D rajzpozíciója.
        self.pos = {}
        gs_names = list(self.ground_stations.keys())
        sat_names = [sd.name for sd in self.satellites]

        #körön helyezzük el őket, mert így a sat-sat kapcsolatok
        # sokkal áttekinthetőbben látszanak, mint egy egyenes sorban.
        sat_radius = 1.0
        sat_angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, len(sat_names), endpoint=False)
        for sat_name, angle in zip(sat_names, sat_angles):
            self.pos[sat_name] = (
                sat_radius * np.cos(angle),
                sat_radius * np.sin(angle),
            )

        # Azért külön íven vannak, hogy jól elkülönüljenek a műholdaktól.
        gs_radius = 0.55
        if len(gs_names) == 1:
            gs_angles = [3 * np.pi / 2]
        else:
            gs_angles = np.linspace(7 * np.pi / 6, 11 * np.pi / 6, len(gs_names))

        for gs_name, angle in zip(gs_names, gs_angles):
            self.pos[gs_name] = (
                gs_radius * np.cos(angle),
                gs_radius * np.sin(angle),
            )

        #csomópontok kirajzolása
        sat_x = [self.pos[n][0] for n in sat_names]
        sat_y = [self.pos[n][1] for n in sat_names]
        ax.scatter(sat_x, sat_y, s=150, c='red', marker='^', label='Satellites', zorder=5)

        gs_x = [self.pos[n][0] for n in gs_names]
        gs_y = [self.pos[n][1] for n in gs_names]
        ax.scatter(gs_x, gs_y, s=300, c='blue', label='Ground Stations', zorder=5)

        # A műholdfeliratokat a körön kívül kicsit kijjebb tesszük,
        # hogy ne lógjanak bele a csomópontokba.
        #feliratok
        for sat_name in sat_names:
            x, y = self.pos[sat_name]
            angle = np.arctan2(y, x)
            label_r = 1.18
            lx = label_r * np.cos(angle)
            ly = label_r * np.sin(angle)
            ax.text(lx, ly, self._short_sat_label(sat_name), ha='center', va='center', fontsize=8)

        # A földi állomások felirata közvetlenül a pont alatt jelenik meg.
        for gs_name in gs_names:
            x, y = self.pos[gs_name]
            ax.text(x, y - 0.12, gs_name, ha='center', va='center', fontsize=9)


        # A hálózati nézet legyen torzításmentes, tehát azonos skálát használjon x és y irányban.
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)

        # Ide gyűjtjük a pillanatnyilag kirajzolt élek vonalait,
        # hogy a következő frame előtt törölni tudjuk őket.
        edge_lines = []

        # Információs szöveg a nézet tetején.
        info_text = ax.text(
            0.5,
            0.95,
            "",
            fontsize=10,
            transform=ax.transAxes,
            ha='center',
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray')
        )

        def update_net(frame):
            # Az aktuális hálózati frame kirajzolása.
            self.current_frame = frame

            # Előző frame éleinek törlése.
            for line in edge_lines:
                line.remove()
            edge_lines.clear()

            # Az adott időpillanathoz tartozó snapshot-gráf.
            G = self.dynamic_graphs[frame]

            sat_sat_count = 0
            sat_ground_count = 0

            # Az összes él kirajzolása az aktuális gráfból.
            for u, v, attrs in G.edges(data=True):
                x_values = [self.pos[u][0], self.pos[v][0]]
                y_values = [self.pos[u][1], self.pos[v][1]]

                # Ha az élhez tartozik explicit link_type attribútum,
                # akkor azt használjuk.
                edge_type = attrs.get('link_type')

                # Ha nincs explicit él-típus, akkor a két végpont típusa alapján
                # következtetünk: satellite-satellite -> sat_sat, minden más -> sat_ground.
                if edge_type is None:
                    u_type = G.nodes[u].get('type')
                    v_type = G.nodes[v].get('type')
                    if u_type == 'satellite' and v_type == 'satellite':
                        edge_type = 'sat_sat'
                    else:
                        edge_type = 'sat_ground'

                # A két linktípus külön stílusban rajzolódik.
                if edge_type == 'sat_sat':
                    line, = ax.plot(
                        x_values,
                        y_values,
                        '-',
                        color='dimgray',
                        alpha=0.8,
                        linewidth=1.8,
                        zorder=1
                    )
                    sat_sat_count += 1
                else:
                    line, = ax.plot(
                        x_values,
                        y_values,
                        '--',
                        color='royalblue',
                        alpha=0.8,
                        linewidth=1.6,
                        zorder=1
                    )
                    sat_ground_count += 1

                edge_lines.append(line)

            # Statisztika kiírása az aktuális frame-ről.
            info_text.set_text(
                f"Time Step: {frame} min | Active Connections: {len(G.edges())} "
                f"(sat-sat: {sat_sat_count}, sat-ground: {sat_ground_count})"
            )
            return edge_lines + [info_text]

        # Eltesszük, hogy nézetváltáskor közvetlenül is meg lehessen hívni.
        self._update_net = update_net

        # Hálózati animáció létrehozása.
        self.anim_net = FuncAnimation(
            self.fig,
            update_net,
            frames=self._frame_iter(0),
            interval=50,
            blit=False,
            cache_frame_data=False
        )

        # Vissza gomb.
        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        # Szünet / folytatás gomb.
        pause_ax = self.fig.add_axes([0.12, 0.01, 0.1, 0.05])
        pause_btn = Button(pause_ax, "Pause")
        pause_btn.on_clicked(self.toggle_animation)

        self.views["network"] = {
            "axes": ax,
            "widgets": [back_btn, pause_btn]
        }

        # Induláskor ne fusson a hálózati animáció automatikusan,
        # csak ha erre a nézetre váltunk.
        self.anim_net.event_source.stop()

    def _create_elevation_view(self):
        # Eleváció-idősor nézet.
        ax = self.fig.add_subplot(111)
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        plotted_lines = 0
        for i, sd in enumerate(self.satellites):
            for gs_name, data in sd.station_data.items():
                # Csak azokat a kapcsolatokat rajzoljuk, ahol ténylegesen volt pass.
                if len(data['passes']) > 0:
                    ax.plot(
                        data['elevation_deg'],
                        color=colors[plotted_lines % len(colors)],
                        label=f"{sd.name[:8]} - {gs_name}",
                        alpha=0.7
                    )
                    plotted_lines += 1

        # Küszöbvonal a láthatósági / aktív kapcsolati határhoz.
        ax.axhline(self.threshold, color='red', linestyle='--', label='Threshold')
        ax.set_title("Elevation vs Time (Only Active Passes)")
        ax.set_xlabel("Time step (min)")
        ax.set_ylabel("Elevation (deg)")

        if plotted_lines > 0:
            ax.legend(loc='upper right', fontsize='x-small', ncol=2)

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        self.views["elevation"] = {
            "axes": ax,
            "widgets": [back_btn]
        }

    def toggle_animation(self, event):
        # Az animáció futását kapcsolja ki / be.
        self.running = not self.running

        # Mindig csak az éppen látható animált nézetre hat.
        if self.views["map"]["axes"].get_visible():
            if self.running:
                self.anim_map.event_source.start()
            else:
                self.anim_map.event_source.stop()

        elif self.views["network"]["axes"].get_visible():
            if self.running:
                self.anim_net.event_source.start()
            else:
                self.anim_net.event_source.stop()

    def _create_map_view(self):
        # Földtérképes nézet létrehozása.
        ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
        self.viz.setup_map_axes(ax)
        ax.set_title("2D Satellite Constellation Map")

        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        sat_points = []
        link_lines_dict = {}

        # Minden műholdhoz létrehozunk egy pontot a térképen,
        # és minden műhold–állomás párhoz egy potenciális összekötő vonalat.
        for i, sd in enumerate(self.satellites):
            color = colors[i % len(colors)]
            pt, = ax.plot([], [], 'o', color=color, transform=ccrs.PlateCarree(), markersize=5)
            sat_points.append(pt)

            link_lines_dict[i] = {}
            for gs_name in self.ground_stations.keys():
                ln, = ax.plot([], [], '-', color=color, transform=ccrs.PlateCarree(), linewidth=1.5, alpha=0.6)
                link_lines_dict[i][gs_name] = ln

        # Információs szöveg a térkép bal alsó részén.
        info_text = ax.text(-170, -80, "", transform=ccrs.PlateCarree(), fontsize=8,
                            bbox=dict(facecolor='white', alpha=0.8))

        def update_map(frame):
            # Az aktuális térképes frame kirajzolása.
            self.current_frame = frame

            lines, status_lines = [], []
            for i, sd in enumerate(self.satellites):
                lat = self.viz.sub_lats_list[i][frame]
                lon = self.viz.sub_lons_list[i][frame]
                sat_points[i].set_data([lon], [lat])
                lines.append(sat_points[i])

                active_links = []
                for gs_name, gs_obj in self.ground_stations.items():
                    elev = sd.station_data[gs_name]['elevation_deg'][frame]
                    ln = link_lines_dict[i][gs_name]

                    # Csak akkor rajzoljuk meg a linket, ha az eleváció a küszöb fölött van.
                    if elev > self.threshold:
                        gs_lat = gs_obj.latitude.degrees
                        gs_lon = gs_obj.longitude.degrees
                        ln.set_data([gs_lon, lon], [gs_lat, lat])
                        active_links.append(f"{gs_name} ({elev:.1f}°)")
                    else:
                        ln.set_data([], [])
                    lines.append(ln)

                # Az info panelre csak azokat a műholdakat írjuk ki,
                # amelyeknek épp van aktív föld–műhold kapcsolatuk.
                if active_links:
                    status_lines.append(f"{sd.name[:8]}: " + ", ".join(active_links))

            status_display = "\n".join(status_lines) if status_lines else "No active links."
            info_text.set_text(f"Step: {frame} min\n" + status_display)
            lines.append(info_text)

            return lines

        # Eltesszük a frissítő függvényt, hogy nézetváltáskor közvetlenül is használhassuk.
        self._update_map = update_map

        # Térképes animáció létrehozása.
        self.anim_map = FuncAnimation(
            self.fig,
            update_map,
            frames=self._frame_iter(0),
            interval=50,
            blit=False,
            cache_frame_data=False
        )

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        pause_ax = self.fig.add_axes([0.12, 0.01, 0.1, 0.05])
        pause_btn = Button(pause_ax, "Pause")
        pause_btn.on_clicked(self.toggle_animation)

        self.views["map"] = {
            "axes": ax,
            "widgets": [back_btn, pause_btn]
        }

        #Induláskor ez se fusson, csak ha megnyitjuk ezt a nézetet.
        self.anim_map.event_source.stop()

    def _create_keyrate_view(self):
        ax = self.fig.add_subplot(111)
        ax.set_visible(False)

        #teljes tengelyt töröljük, és helyette 2 altengelyt csinálunk ugyanebben a figurában.
        ax.remove()

        ax1 = self.fig.add_axes([0.10, 0.56, 0.82, 0.32])
        ax2 = self.fig.add_axes([0.10, 0.14, 0.82, 0.32])

        def db_to_eta(loss_db):
            return 10.0 ** (-loss_db / 10.0)

        #Fig 5szerű: single link
        single_link_losses_db = [45, 50, 55, 60]
        mu_values = np.linspace(self.key_model.mu_min, self.key_model.mu_max, 220)

        for loss_dB in single_link_losses_db:
            eta = db_to_eta(loss_dB)
            sweep = self.key_model.sweep_mu(eta, mu_values=mu_values)

            ax1.plot(
                sweep["pair_rate_hz"] / 1e6,
                sweep["eskr"],
                label=f"{loss_dB} dB"
            )

            best_idx = np.argmax(sweep["eskr"])
            ax1.plot(
                sweep["pair_rate_hz"][best_idx] / 1e6,
                sweep["eskr"][best_idx],
                'o'
            )

        ax1.set_title("Fig. 5-style: achievable secure key rate over a single link")
        ax1.set_xlabel("Photon pair rate [Mcps]")
        ax1.set_ylabel("ESKR [bit/s]")
        ax1.grid(True, alpha=0.3)
        ax1.legend(title="Single-link loss")

        # symmetric dual downlink
        dual_link_losses_db = [20, 25, 30]
        current_pair_rate_mcps = np.nan

        for loss_db in dual_link_losses_db:
            eta_single = db_to_eta(loss_db)
            sweep = self.key_model.sweep_mu_symmetric_dual_downlink(
                eta_single,
                mu_values=mu_values
            )

            print(
                f"dual loss: {loss_db} dB per link, "
                f"eta_single={eta_single:.2e}, "
                f"eta_dual={eta_single * eta_single:.2e}, "
                f"max ESKR={np.max(sweep['eskr']):.3e}"
            )

            ax2.plot(
                sweep["pair_rate_hz"] / 1e6,
                sweep["eskr"],
                label=f"{loss_db} dB per link"
            )

            best_idx = np.argmax(sweep["eskr"])
            ax2.plot(
                sweep["pair_rate_hz"][best_idx] / 1e6,
                sweep["eskr"][best_idx],
                'o'
            )

        ax2.axvspan(4.0, 7.0, alpha=0.15, label="example dual-downlink region")

        ax2.set_title("Fig. 6-style: achievable secure key rate in symmetric dual downlink")
        ax2.set_xlabel("Photon pair generation rate [Mcps]")
        ax2.set_ylabel("ESKR [bit/s]")
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize='small', ncol=2)
        ax2.set_ylim(bottom=0)

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        self.views["keyrate"] = {
            "axes": ax1,   # csak egy tengelyt kell regisztrálni a váltáshoz
            "widgets": [back_btn]
        }

        # kézzel eltesszük a második tengelyt is, hogy kapcsolni tudjuk a láthatóságát
        self.views["keyrate"]["extra_axes"] = [ax2]

        ax1.set_visible(False)
        ax2.set_visible(False)


    def _path_bottleneck_eskr(self, G, path):
        values = []

        for u, v in zip(path[:-1], path[1:]):
            edge_data = G[u][v]
            values.append(float(edge_data.get("weight", 0.0)))

        if len(values) == 0:
            return 0.0

        return min(values)
    
    def _create_network_eskr_view(self):
        # Teljes hálózati ESKR-idősor nézet.
        # Minden időpillanatban összeadjuk az aktív élek ESKR értékét.
        ax = self.fig.add_subplot(111)

        total_eskr = []
        #sat_ground_eskr = []
        #sat_sat_eskr = []

        gs_names = list(self.ground_stations.keys())

        for G in self.dynamic_graphs:
            timestep_total = 0.0

            for i in range(len(gs_names)):
                for j in range(i + 1, len(gs_names)):
                    src_gs = gs_names[i]
                    dst_gs = gs_names[j]

                    if src_gs not in G or dst_gs not in G:
                        continue

                    result = self._maxflow_mincut_between(G, src_gs, dst_gs)
                    timestep_total += result["flow_value"]


            total_eskr.append(timestep_total)



        time_steps = np.arange(len(total_eskr))
        total_eskr = np.asarray(total_eskr, dtype=float)

        total_plot = np.where(total_eskr > 0, total_eskr, np.nan)

        ax.plot(time_steps, total_plot, label="Ground-station end-to-end ESKR", linewidth=2)

        ax.set_title("Sum of End-to-end Ground Station ESKR over Time")
        ax.set_xlabel("Time step [min]")
        ax.set_ylabel("End-to-end ESKR [bit/s]")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Összes generált kulcs becslése.
        # A szimulációban egy time step jelenleg 1 perc, tehát dt = 60 s.
        dt_s = 60.0
        total_generated_bits = np.sum(total_eskr) * dt_s

        ax.text(
            0.02,
            0.95,
            f"Generated key over simulation: {total_generated_bits:.2e} bit",
            transform=ax.transAxes,
            fontsize=9,
            va="top",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="gray")
        )

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        self.views["network_eskr"] = {
            "axes": ax,
            "widgets": [back_btn]
        }

        ax.set_visible(False)

    def _compute_pair_flow(self, src_gs, dst_gs):
        """
        Két földi állomás közötti időfüggő end-to-end kapacitás.

        Itt már nem egyetlen legrövidebb utat keresünk,
        hanem max-flow algoritmussal számoljuk ki,
        hogy az aktuális műholdas hálózatban összesen mekkora ESKR
        vihető át src_gs és dst_gs között.

        A min-cut pedig megmutatja az aktuális szűk keresztmetszetet.
        """

        flow_eskr = []
        cut_values = []
        cut_edge_labels = []

        for G in self.dynamic_graphs:
            result = self._maxflow_mincut_between(G, src_gs, dst_gs)

            flow_value = result["flow_value"]
            cut_value = result["cut_value"]
            cut_edges = result["cut_edges"]

            flow_eskr.append(flow_value)
            cut_values.append(cut_value)

            if len(cut_edges) == 0:
                cut_edge_labels.append("")
            else:
                labels = []
                for e in cut_edges:
                    labels.append(
                        f"{e['src']} -> {e['dst']} ({e['capacity']:.2f} bit/s)"
                    )
                cut_edge_labels.append("; ".join(labels))

        return flow_eskr, cut_values, cut_edge_labels
    
    def _create_pair_flow_view(self):
        ax = self.fig.add_subplot(111)

        src_gs = "Budapest"
        dst_gs = "N'Djamena"

        flow_eskr, cut_values, cut_edge_labels = self._compute_pair_flow(src_gs, dst_gs)

        flow_eskr = np.asarray(flow_eskr, dtype=float)
        flow_plot = np.where(flow_eskr > 0, flow_eskr, np.nan)

        time_steps = np.arange(len(flow_eskr))

        ax.plot(
            time_steps,
            flow_plot,
            linewidth=2,
            label=f"{src_gs} -> {dst_gs} max-flow ESKR"
        )

        dt_s = 60.0
        generated_bits = np.sum(flow_eskr) * dt_s
        active_steps = np.sum(flow_eskr > 0)

        ax.set_title(f"End-to-end Flow: from {src_gs} to {dst_gs}")
        ax.set_xlabel("Time step (min)")
        ax.set_ylabel("Max-flow ESKR (bit/s)")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend()

        ax.text(
            0.02,
            0.95,
            f"Generated key: {generated_bits:.2e} bit\n"
            f"Active time steps: {active_steps}\n"
            f"Active time: {active_steps:.0f} min",
            transform=ax.transAxes,
            fontsize=9,
            va="top",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="gray")
        )

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "Back")
        back_btn.on_clicked(lambda e: self._deferred_switch("menu"))

        self.views["pair_flow"] = {
            "axes": ax,
            "widgets": [back_btn]
        }

        ax.set_visible(False)

    def _find_multisat_pair_flows(self, min_satellites=2, min_rate=0.0):
        results = []

        gs_names = list(self.ground_stations.keys())

        for src_gs in gs_names:
            for dst_gs in gs_names:
                if src_gs >= dst_gs:
                    continue

                active_steps = 0
                total_generated_bits = 0.0
                best_rate = 0.0
                best_frame = None
                best_path = None
                best_satellite_count = 0

                for frame, G in enumerate(self.dynamic_graphs):
                    if src_gs not in G or dst_gs not in G:
                        continue

                    # Csak pozitív ESKR-es éleket használunk a flow-hoz
                    H = nx.Graph()
                    H.add_nodes_from(G.nodes(data=True))

                    for u, v, attrs in G.edges(data=True):
                        kr = float(attrs.get("weight", 0.0))
                        if kr > min_rate:
                            H.add_edge(u, v, **attrs)

                    if src_gs not in H or dst_gs not in H:
                        continue

                    try:
                        path = nx.shortest_path(
                            H,
                            source=src_gs,
                            target=dst_gs,
                            weight="routing_cost"
                        )
                    except nx.NetworkXNoPath:
                        continue

                    satellite_count = 0
                    for node in path:
                        if H.nodes[node].get("type") == "satellite":
                            satellite_count += 1

                    if satellite_count < min_satellites:
                        continue

                    edge_rates = []
                    for u, v in zip(path[:-1], path[1:]):
                        edge_rates.append(float(H[u][v].get("weight", 0.0)))

                    if not edge_rates:
                        continue

                    bottleneck = min(edge_rates)

                    if bottleneck <= min_rate:
                        continue

                    active_steps += 1
                    total_generated_bits += bottleneck * 60.0

                    if bottleneck > best_rate:
                        best_rate = bottleneck
                        best_frame = frame
                        best_path = path
                        best_satellite_count = satellite_count

                if active_steps > 0:
                    results.append({
                        "src": src_gs,
                        "dst": dst_gs,
                        "active_steps": active_steps,
                        "generated_bits": total_generated_bits,
                        "best_rate": best_rate,
                        "best_frame": best_frame,
                        "best_path": best_path,
                        "satellite_count": best_satellite_count,
                    })

        results.sort(
            key=lambda r: (r["active_steps"], r["generated_bits"], r["best_rate"]),
            reverse=True
        )

        return results

    def _capacity_graph_from_snapshot(self, G, min_rate=0.0):
        
        #Az aktuális időpillanat NetworkX gráfjából kapacitásgráfot készít.
        H = nx.DiGraph() #irányított gráf
        H.add_nodes_from(G.nodes(data=True))

        for u, v, attrs in G.edges(data=True):
            capacity = float(attrs.get("weight", 0.0))

            if capacity <= min_rate:
                continue

            if not np.isfinite(capacity):
                continue

            H.add_edge(u, v, capacity=capacity, **attrs)
            H.add_edge(v, u, capacity=capacity, **attrs)

        return H


    def _maxflow_mincut_between(self, G, src, dst, min_rate=0.0):

        H = self._capacity_graph_from_snapshot(G, min_rate=min_rate)

        if src not in H or dst not in H:
            return {
                "flow_value": 0.0,
                "cut_value": 0.0,
                "cut_edges": [],
                "reachable": set(),
                "non_reachable": set(),
            }

        try:
            flow_value, flow_dict = nx.maximum_flow(
                H,
                src,
                dst,
                capacity="capacity"
            )

            cut_value, partition = nx.minimum_cut(
                H,
                src,
                dst,
                capacity="capacity"
            )

            reachable, non_reachable = partition

            cut_edges = []
            for u in reachable:
                for v in H.successors(u):
                    if v in non_reachable:
                        cut_edges.append(
                            {
                                "src": u,
                                "dst": v,
                                "capacity": float(H[u][v]["capacity"]),
                                "link_type": H[u][v].get("link_type", "unknown"),
                            }
                        )

            return {
                "flow_value": float(flow_value),
                "cut_value": float(cut_value),
                "cut_edges": cut_edges,
                "reachable": reachable,
                "non_reachable": non_reachable,
            }

        except nx.NetworkXError:
            return {
                "flow_value": 0.0, #maximális átvihető ESKR [bit/s]
                "cut_value": 0.0, #minimális vágás kapacitása [bit/s]
                "cut_edges": [], #azok az élek, amelyek a min-cut vágásban vannak
                "reachable": set(),
                "non_reachable": set(),
            }

    def run(self):
        # A matplotlib fő eseményciklusa.
        plt.show()
